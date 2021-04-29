import pandas as pd
from shapely import wkb
from shapely.geometry import LineString
import geopandas as gp
import hashlib
from tqdm import tqdm
import sqlite3
import datetime
from itertools import tee
import numpy as np
import os, csv
# from sklearn.metrics.pairwise import haversine_distances
from haversine import haversine, Unit

# METERS_PER_DEGREE_LATITUDE = 111070.34306591158
# METERS_PER_DEGREE_LONGITUDE = 83044.98918812413
EARTH_RADIUS = 6371000 # meters


def convert_location(x):
    point = wkb.loads(x, hex=True)
    return point.x, point.y


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
                ['route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed',
                 'distance']
            ]
        else:
            inbound_df = inbound_df[
                ['route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed']
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
            ['route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed',
             'distance']
        ]
    else:
        all_df = all_df[
            ['route_slug', 'latitude', 'longitude', 'altitude', 'timestamp', 'bearing', 'speed']
        ]
    return all_df


def load_directory(
        dir_path, boundary,
        output_dir, shape_path,
        has_distance=True,
        min_dist_threshold=5,
        max_dist_threshold=170,
        max_time_threshold=10,
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
    all_df['pre_route_slug'] = all_df.route_slug.shift(1)
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
    all_df.reset_index(drop=True, inplace=True)

    for index, row in tqdm(all_df.iterrows(), total=len(all_df)):

        if any([
            row['route_slug'] != row['pre_route_slug'],
            row['delta_time'] > max_time_threshold,
            row['avg_speed'] > max_spd_threshold,
            row['delta_dist'] > max_dist_threshold
        ]):
            last = index
            all_df.iloc[first:last]['ntraj_points'] = last - first
            all_df.iloc[first:last]['route_id'] = last_route_id
            last_route_id += 1
            first = index
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


with open('./new-old-version/utils/bounding_box.txt', 'r') as bbx_file:
    north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

boundary = dict(
    east=east,
    west=west,
    north=north,
    south=south
)

_ = load_directory(
    dir_path='./loc_sample/teh_uni_loc_sample/',
    boundary=boundary,
    output_dir='./data/gps-csv/sample-area',
    shape_path='./data/trajectories/trajs.shp',
    has_distance=True,
    large_size=False
)