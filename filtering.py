import pandas as pd
from shapely import wkb
from shapely.geometry import LineString
import geopandas as gp
import hashlib
import datetime
import numpy as np
import os, csv


def modify_data(file_path, boundary, route_mapping):
    data = pd.read_parquet(file_path)
    trajectories = []
    temp_point = []
    print(file_path)
    last_index = len(route_mapping)
    #todo: this loop is just for one way_id
    for i in range(len(data['device_id'])):
        point = wkb.loads(data.iloc[i]['location'], hex=True)
        if boundary['west'] < point.x < boundary['east'] and boundary['south'] < point.y < boundary['north']:
            temp_point.append([
                point.x,
                point.y,
                datetime.datetime.fromtimestamp(int(data.iloc[i]['timestamp']) / 1000),
                data.iloc[i]['bearing']
            ])
        else:
            continue
        #todo: change data index to one time by saving nest data index
        if data.iloc[i]['route_slug'] != data.iloc[i+1]['route_slug']:
            if data.iloc[i]['route_slug'] in route_mapping.keys():
                route_id = route_mapping[data.iloc[i]['route_slug']]
            else:
                route_mapping[data.iloc[i]['route_slug']] = last_index
                route_id = last_index
                last_index += 1
            if len(temp_point) > 1:
                trajectories.append(
                    (
                        # np.int64(int(hashlib.md5(data.iloc[i]['route_slug'].encode('utf-8')).hexdigest(), 16) % (10**9)),
                        route_id,
                        sorted(temp_point, key=lambda x: x[2])
                    )
                )
                temp_point = []
    if len(trajectories) == 0:
        print('No bounded points')
    return trajectories, route_mapping


def load_data(file_path, boundary, file_dist):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    prefix = ''.join(str(int(value)) for value in [
        boundary['west'], boundary['east'], boundary['south'], boundary['north']
    ])
    route_mapping = {}
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        if not os.path.exists(file_dist + '/' + prefix):
            os.makedirs(file_dist + '/' + prefix)
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.snappy'):
                continue
            trajectories, route_mapping = modify_data(os.path.join(file_path, dir_name, file), boundary, route_mapping)
            if not trajectories:
                continue
            file_name = file_dist + '/' + prefix + '/' + file.split('.snappy')[0]+'.csv'
            with open(file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                writer.writerow(['route_id', 'longitude', 'latitude', 'timestamp', 'bearing'])
                for trajectory in trajectories:
                    for point in trajectory[1]:
                        writer.writerow([trajectory[0]]+point)
    return file_dist


def make_trajs(file_path):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    trajectories = []
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.csv'):
                continue
            data = pd.read_csv(os.path.join(file_path, dir_name, file), sep=',', header=0, engine='python')
            line = []
            bearings = []
            for i in range(len(data)-1):
                point = data.iloc[i]
                line.append((point['longitude'], point['latitude']))
                bearings.append(str(point['bearing']))
                if point['route_id'] != data.iloc[i+1]['route_id']:
                    traj_line = LineString(line)
                    trajectories.append((point['route_id'], traj_line, ','.join(bearings)))
                    line = []
                    bearings = []
    return trajectories


def trajToShape(source_path, dist_path):
    trajectories = make_trajs(source_path)
    df = pd.DataFrame(trajectories, columns=['id', 'geometry', 'bearing'])
    df = gp.GeoDataFrame(df, geometry='geometry')
    df.to_file(dist_path, driver='ESRI Shapefile')