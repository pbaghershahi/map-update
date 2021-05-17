import pandas as pd
from shapely import wkb
from shapely.geometry import LineString
import geopandas as gp
from tqdm import tqdm
import glob
import hashlib
import sqlite3
import datetime
from itertools import tee
import numpy as np
import os, csv, sys
# from sklearn.metrics.pairwise import haversine_distances
from haversine import haversine, Unit

# METERS_PER_DEGREE_LATITUDE = 111070.34306591158
# METERS_PER_DEGREE_LONGITUDE = 83044.98918812413
EARTH_RADIUS = 6371000 # meters


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def convert_location(x):
    point = wkb.loads(x, hex=True)
    return point.x, point.y


def thresh_determiner(obj_list, thresh_percent=0.95, n_bins=100):
    bin_values, edges = np.histogram(obj_list, bins=n_bins)
    bin_cum = np.cumsum(bin_values)
    bin_cum = bin_cum / bin_cum[-1]
    threshold = int(edges[np.argmin(abs(bin_cum - thresh_percent)) + 1])
    return threshold


def insert_nodes(node1, node2, n):
    latitudes = np.linspace(node1[0], node2[0], n)
    longitudes = np.linspace(node1[1], node2[1], n)
    nodes = list(zip(longitudes, latitudes))
    return nodes


# def dist_measure(x, y):
#     return np.sqrt(((x[0]-y[0])*METERS_PER_DEGREE_LONGITUDE)**2 + ((x[1]-y[1])*METERS_PER_DEGREE_LATITUDE)**2)
def dist_measure(x, y):
    return haversine(x[:2][::-1], y[:2][::-1], unit=Unit.METERS)


def spd_measure(x, y):
    return dist_measure(x, y)/max((y[3]-x[3]).seconds, 1)


def time_preprocess(trip, time_threshold=20):
    filtered_trip = []
    counter = 0
    for org, dest in pairwise(trip):
        delta = (dest[3]-org[3]).seconds
        filtered_trip.append(org)
        counter += 1
        if delta > time_threshold:
            break
        if counter == len(trip)-1:
            filtered_trip.append(dest)
    return filtered_trip


def dist_preprocess(trip, max_dist_threshold=170, min_dist_threshold=2):
    filtered_trip = []
    while len(trip) > 1:
        org = trip.pop(0)
        delta = dist_measure(org, trip[0])
        if delta < min_dist_threshold:
            _ = trip.pop(0)
            trip.insert(0, org)
            continue
        filtered_trip.append(org)
        if delta > max_dist_threshold:
            break
        if len(trip) == 1:
            filtered_trip.append(trip.pop())
    return filtered_trip


def spd_preprocess(trip, max_spd_threshold=26, min_spd_threshold=2):
    #note: this function just filter data based on avergae speed between two points, not based on the point gps point speed
    filtered_trip = []
    counter = 0
    for org, dest in pairwise(trip):
        delta = spd_measure(org, dest)
        filtered_trip.append(org)
        counter += 1
        if delta > max_spd_threshold or delta < min_spd_threshold:
            break
        if counter == len(trip)-1:
            filtered_trip.append(dest)
    return filtered_trip


def preprocess(trip, **kwargs):
    temp_trip = time_preprocess(
        trip,
        kwargs['time_threshold'] if 'time_threshold' in kwargs else 20
    )
    temp_trip = dist_preprocess(
        temp_trip,
        kwargs['max_dist_threshold'] if 'max_dist_threshold' in kwargs else 170,
        kwargs['min_dist_threshold'] if 'min_dist_threshold' in kwargs else 5
    )
    temp_trip = spd_preprocess(
        temp_trip,
        kwargs['max_spd_threshold'] if 'max_spd_threshold' in kwargs else 26,
        kwargs['min_spd_threshold'] if 'min_spd_threshold' in kwargs else 2
    )
    return temp_trip


def modify_data(file_path, boundary, global_index, **kwargs):
    print(file_path)
    data = pd.read_parquet(file_path)
    # data.sort_values(['route_slug'], inplace=True)
    # data.reset_index(drop=True, inplace=True)

    data.timestamp = data.timestamp.apply(
        lambda x: datetime.datetime.fromtimestamp(int(x) / 1000)
    )
    data.location = data.location.apply(
        lambda x: convert_location(x)
    )
    data['in_bound'] = data.location.apply(
        lambda x: boundary['west'] < x[0] < boundary['east'] and boundary['south'] < x[1] < boundary['north']
    )
    trajectories = []
    temp_trip = []
    # last_index = len(route_mapping)

    # for i in range(len(data['device_id'])):
    for i in range(len(data)-1):
        if data.iloc[i]['in_bound']:
            temp_trip.append([
                data.iloc[i]['location'][0],
                data.iloc[i]['location'][1],
                data.iloc[i]['altitude'],
                data.iloc[i]['timestamp'],
                data.iloc[i]['bearing'],
                data.iloc[i]['speed']
            ])
        else:
            if len(temp_trip) > 1:
                temp_trip = sorted(temp_trip, key=lambda x: x[3])
                temp_trip = preprocess(temp_trip, **kwargs)
                if len(temp_trip) > 1:
                    # route_id = global_index
                    # if data.iloc[i]['route_slug'] in route_mapping.keys():
                    #     route_id = route_mapping[data.iloc[i]['route_slug']]
                    # else:
                    #     route_mapping[data.iloc[i]['route_slug']] = last_index
                    #     route_id = last_index
                    #     last_index += 1
                    trajectories.append(
                        (
                            # np.int64(int(hashlib.md5(data.iloc[i]['route_slug'].encode('utf-8')).hexdigest(), 16) % (10**9)),
                            global_index,
                            temp_trip
                        )
                    )
                    global_index += 1
            temp_trip = []
            continue

        if data.iloc[i]['route_slug'] != data.iloc[i+1]['route_slug']:
            if len(temp_trip) > 1:
                temp_trip = sorted(temp_trip, key=lambda x: x[3])
                temp_trip = preprocess(temp_trip, **kwargs)
                if len(temp_trip) > 1:
                    # if data.iloc[i]['route_slug'] in route_mapping.keys():
                    #     route_id = route_mapping[data.iloc[i]['route_slug']]
                    # else:
                    #     route_mapping[data.iloc[i]['route_slug']] = last_index
                    #     route_id = last_index
                    #     last_index += 1
                    trajectories.append(
                        (
                            global_index,
                            temp_trip
                        )
                    )
                    global_index += 1
            temp_trip = []
    if len(trajectories) == 0:
        print('No bounded points')
    return trajectories, global_index


def load_data(file_path, boundary, file_dist):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    prefix = ''.join(str(int(value)) for value in [
        boundary['west'], boundary['east'], boundary['south'], boundary['north']
    ])
    # route_mapping = {}
    global_index = 0
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        if not os.path.exists(file_dist + '/' + prefix):
            os.makedirs(file_dist + '/' + prefix)
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.parquet'):
                continue
            # trajectories, route_mapping = modify_data(os.path.join(file_path, dir_name, file), boundary, route_mapping)
            trajectories, global_index = modify_data(os.path.join(file_path, dir_name, file), boundary, global_index)
            if not trajectories:
                continue
            file_name = file_dist + '/' + prefix + '/' + file.split('.snappy')[0]+'.csv'
            with open(file_name, 'w') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                csv_writer.writerow(['route_id', 'longitude', 'latitude', 'altitude', 'timestamp', 'bearing', 'speed'])
                for trajectory in trajectories:
                    for point in trajectory[1]:
                        csv_writer.writerow([trajectory[0]]+point)
    return file_dist + '/' + prefix + '/'


def make_trajs(file_path):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    trajectories = []
    # print('here in make_trajs')
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        # print(files)
        for file in tqdm(files, total=len(files)):
            # print('size trajs:', sys.getsizeof(trajectories))
            # print(file)
            # print('len trajs:', len(trajectories))
            if not file.endswith('.csv'):
                # print('not found csv')
                continue
            data = pd.read_csv(os.path.join(file_path, dir_name, file), sep=',', header=0, engine='python')
            # print('size data:', sys.getsizeof(data))
            # print('len data:', len(data))
            altitudes = []
            line = []
            bearings = []
            speeds = []
            for i in range(len(data)-1):
                point = data.iloc[i]
                line.append((point['longitude'], point['latitude']))
                altitudes.append(str(point['altitude']))
                bearings.append(str(point['bearing']))
                speeds.append(str(point['speed']))
                # print(len(line), end='\r')
                if point['route_id'] != data.iloc[i+1]['route_id']:
                    # print('size innerdata:', sys.getsizeof(line), sys.getsizeof(altitudes), sys.getsizeof(bearings), sys.getsizeof(speeds))
                    traj_line = LineString(line)
                    trajectories.append((point['route_id'], traj_line, ','.join(altitudes), ','.join(bearings), ','.join(speeds)))
                    # trajectories.append((point['route_id'], traj_line, ','.join(bearings), ','.join(speeds)))
                    line = []
                    bearings = []
                    speeds = []
                    altitudes = []
    return trajectories

def csv2trajs(dir_path):
    all_files = sorted(glob.glob(os.path.join(dir_path, "*.csv")))
    each_file_df = (pd.read_csv(f) for f in all_files)
    all_trajs = pd.concat(each_file_df, ignore_index=True)
    all_trajs['pre_route_id'] = all_trajs.route_id.shift(1)
    all_trajs = all_trajs[1:]
    all_trajs['pre_route_id'] = all_trajs['pre_route_id'].astype(np.int32)
    trajs_list = []
    first, last = 0, 0
    list2str = lambda x: ','.join([str(y) for y in x])
    all_trajs.reset_index(drop=True, inplace=True)
    for index, row in tqdm(all_trajs.iterrows(), total=len(all_trajs)):
        if row['route_id'] != row['pre_route_id']:
            last = index
            idx_df = all_trajs.iloc[first:last]
            traj_list = list(zip(idx_df.longitude.values, idx_df.latitude.values))
            if len(traj_list) > 1:
                trajs_list.append(
                    (row['pre_route_id'], LineString(traj_list), list2str(idx_df.altitude.tolist()),
                     list2str(idx_df.bearing.tolist()), list2str(idx_df.speed.tolist()))
                )
            first = index
    return trajs_list


def trajToShape(source_path, dist_path):
    # trajectories = make_trajs(source_path)
    trajectories = csv2trajs(source_path)
    df = pd.DataFrame(trajectories, columns=['id', 'geometry', 'altitude', 'bearing', 'speed'])
    df = gp.GeoDataFrame(df, geometry='geometry')
    df.to_file(dist_path, driver='ESRI Shapefile')


def load_unmatched(file_path, unmatches, file_dist):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    unmatch_trajs = pd.DataFrame()
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        if not os.path.exists(file_dist + '/unmatched'):
            os.makedirs(file_dist + '/unmatched')
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.csv'):
                continue
            full_path = os.path.join(file_path, dir_name, file)
            print(full_path)
            temp_csv = pd.read_csv(full_path, sep=',', engine='python')
            unmatch_trajs = pd.concat([unmatch_trajs, temp_csv[temp_csv.route_id.isin(unmatches)]])

    file_name = file_dist + '/unmatched/unmatched.csv'
    unmatch_trajs.to_csv(file_name, sep=',', header=True, index=False)
    return file_dist


def edgeToShape(map_dbpath, dist_path, min_length=20, n=5):
    con = sqlite3.connect(map_dbpath)
    edges_df = pd.read_sql_query("SELECT id, in_node, out_node, weight FROM edges", con)
    nodes_df = pd.read_sql_query("SELECT id, latitude, longitude, weight FROM nodes", con)
    nodes_df.set_index('id', drop=True, inplace=True)
    # find the start and end nodes coordinates for each edge of the edges table
    # based on nodes of the nodes table
    # filter edges by minimum length
    edges_df['way_length'] = edges_df.apply(
        lambda row: haversine(
            (nodes_df.loc[row.in_node].latitude, nodes_df.loc[row.in_node].longitude),
            (nodes_df.loc[row.out_node].latitude, nodes_df.loc[row.out_node].longitude),
            unit=Unit.METERS
            ),
        axis=1)
    edges_df = edges_df[edges_df.way_length > min_length]
    edges_df['in_out'] = edges_df[['in_node', 'out_node']].apply(
        lambda x: tuple(y for y in x), axis=1
    )
    unique_indices = []
    for index, row in edges_df.iterrows():
        if row.in_out[::-1] not in unique_indices:
            unique_indices.append(row.in_out)
    edges_df = edges_df[edges_df.in_out.isin(unique_indices)]
    edges_df.reset_index(drop=True, inplace=True)
    edges = pd.DataFrame({'id': edges_df.index + 1})
    edges['way_length'] = edges_df['way_length']
    edges['geometry'] = edges_df.apply(
        lambda row: LineString(
            insert_nodes(
                [nodes_df.loc[row.in_node].latitude, nodes_df.loc[row.in_node].longitude],
                [nodes_df.loc[row.out_node].latitude, nodes_df.loc[row.out_node].longitude],
                n
            )
        ),
    axis=1)
    edges = gp.GeoDataFrame(edges, geometry='geometry')
    edges.to_file(dist_path, driver='ESRI Shapefile')


def read_large_size(dir_path, boundary, has_distance=True):
    all_df = []
    for file_name in sorted(os.listdir(dir_path)):
        if not file_name.endswith('.parquet'):
            continue
        file_path = os.path.join(dir_path, file_name)
        print(file_path)
        inbound_df = pd.read_parquet(file_path)
        inbound_df.location = inbound_df.location.apply(lambda x: convert_location(x))
        inbound_df['longitude'] = inbound_df.location.apply(lambda x: x[0])
        inbound_df['latitude'] = inbound_df.location.apply(lambda x: x[1])
        inbound_df['in_bound'] = inbound_df.location.apply(
            lambda x: boundary['west'] < x[0] < boundary['east'] and boundary['south'] < x[1] < boundary['north']
        )
        inbound_df = inbound_df[inbound_df.in_bound == True]
        if has_distance:
            inbound_df = inbound_df[
                ['device_id', 'route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed',
                 'distance']
            ]
        else:
            inbound_df = inbound_df[
                ['device_id', 'route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed']
            ]
        all_df.append(inbound_df)
    all_df = pd.concat(all_df, ignore_index=True)
    return all_df


def read_small_size(dir_path, boundary, has_distance=True):
    all_df = pd.read_parquet(dir_path)
    all_df.location = all_df.location.apply(lambda x: convert_location(x))
    all_df['longitude'] = all_df.location.apply(lambda x: x[0])
    all_df['latitude'] = all_df.location.apply(lambda x: x[1])
    all_df['in_bound'] = all_df.location.apply(
        lambda x: boundary['west'] < x[0] < boundary['east'] and boundary['south'] < x[1] < boundary['north']
    )
    all_df = all_df[all_df.in_bound == True]
    if has_distance:
        all_df = all_df[
            ['device_id', 'route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed',
             'distance']
        ]
    else:
        all_df = all_df[
            ['device_id', 'route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed']
        ]
    return all_df


def load_directory(
        dir_path, boundary,
        output_dir, shape_path,
        has_distance=True,
        min_dist_threshold=5,
        max_dist_threshold=170,
        max_time_threshold=20,
        max_spd_threshold=26,
        split_threshold=100000,
        large_size=False
):
    if large_size:
        print('loading from large size method')
        all_df = read_large_size(dir_path, boundary, has_distance)
    else:
        print('loading from small size method')
        all_df = read_small_size(dir_path, boundary, has_distance)
    all_df.timestamp = all_df.timestamp.apply(
        lambda x: datetime.datetime.fromtimestamp(int(x) / 1000)
    )
    all_df.sort_values(by=['route_slug', 'timestamp'], inplace=True)
    all_df.reset_index(drop=True, inplace=True)
    all_df['ntraj_points'] = 0
    all_df['route_id'] = 0
    all_df['pr_time'] = all_df.timestamp.shift(1)
    all_df = all_df[1:]
    all_df['delta_time'] = all_df[['timestamp', 'pr_time']].apply(
        lambda x: (x.timestamp - x.pr_time).seconds, axis=1
    )
    if has_distance:
        all_df['pr_distance'] = all_df.distance.shift(1)
        all_df = all_df[1:]
        all_df['delta_dist'] = all_df[['distance', 'pr_distance']].apply(
            lambda x: x.distance - x.pr_distance, axis=1
        )
    else:
        all_df['pr_latitude'] = all_df.latitude.shift(1)
        all_df['pr_longitude'] = all_df.longitude.shift(1)
        all_df = all_df[1:]
        all_df['delta_dist'] = all_df[
            ['latitude', 'longitude', 'pr_latitude', 'pr_longitude']
        ].apply(
            lambda x: haversine(
                (x.latitude, x.longitude),
                (x.pr_latitude, x.pr_longitude),
                unit=Unit.METERS
            ), axis=1
        )
    all_df['avg_speed'] = all_df[['delta_dist', 'delta_time']].apply(
        lambda x: x.delta_dist / max(x.delta_time, 1), axis=1
    )
    print(len(all_df))

    all_df = all_df[all_df.delta_dist > min_dist_threshold]
    last_route_id = 0
    first, last = 0, 0
    for i in range(1, len(all_df)):

        previous = all_df.iloc[i - 1]
        current = all_df.iloc[i]

        if any([
            current['route_slug'] != previous['route_slug'],
            current['delta_time'] > max_time_threshold,
            current['avg_speed'] > max_spd_threshold,
            current['delta_dist'] > max_dist_threshold
        ]):
            last = i
            all_df.iloc[first:last]['ntraj_points'] = last - first
            all_df.iloc[first:last]['route_id'] = last_route_id
            last_route_id += 1
            first = i
    all_df = all_df[all_df.ntraj_points > 1]
    print(len(all_df))
    all_df = all_df[
        [
            'route_id',
            'longitude',
            'latitude',
            'altitude',
            'timestamp',
            'bearing',
            'speed'
        ]
    ]
    idxs = all_df.route_id.unique()
    split_parts = int(len(all_df) / min(split_threshold, len(all_df)))
    splitted_idxs = np.array_split(idxs, split_parts)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for arr in splitted_idxs:
        file_name = os.path.join(output_dir, f'{arr[0]}-{arr[-1]}.csv')
        all_df[all_df.route_id.isin(arr)].to_csv(file_name, sep=',', header=True, index=False)

    trajs_list = []
    list2str = lambda x: ','.join([str(y) for y in x])
    for idx in idxs:
        idx_df = all_df[all_df.route_id == idx]
        traj_list = list(zip(idx_df.longitude.values, idx_df.latitude.values))
        trajs_list.append(
            (idx, LineString(traj_list), list2str(idx_df.altitude.tolist()),
             list2str(idx_df.bearing.tolist()), list2str(idx_df.speed.tolist()))
        )
    df = pd.DataFrame(trajs_list, columns=['id', 'geometry', 'altitude', 'bearing', 'speed'])
    df = gp.GeoDataFrame(df, geometry='geometry')
    df.to_file(shape_path, driver='ESRI Shapefile')
    return all_df