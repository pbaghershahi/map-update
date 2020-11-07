import pandas as pd
from shapely import wkb
from shapely.geometry import LineString
import datetime
import os, csv


def modify_data(file_path, boundary):
    print(file_path)
    data = pd.read_parquet(file_path)
    trajectories = []
    temp_point = []
    counter = 1
    #todo: this loop is just for one way_id
    for i in range(len(data['device_id'])):
        point = wkb.loads(data.iloc[i]['location'], hex=True)
        if boundary['west'] < point.x < boundary['east'] and boundary['south'] < point.y < boundary['north']:
            temp_point.append([
                point.x,
                point.y,
                datetime.datetime.fromtimestamp(int(data.iloc[i]['timestamp']) / 1000)
            ])
        #todo: change data index to one time by saving nest data index
        if data.iloc[i]['route_slug'] != data.iloc[i+1]['route_slug']:
            trajectories.append((data.iloc[i]['route_slug'], sorted(temp_point, key=lambda x: x[2])))
            temp_point = []
        if data.iloc[i]['way_id'] != data.iloc[i + 1]['way_id']:
            if counter > 1:
                break
            counter += 1
    return trajectories


def load_data(file_path, boundry, file_dist):
    if os.path.exists(file_path) is not True:
        print('Path does not exists!')
        return
    prefix = ''.join(str(int(value)) for value in [
        boundry['west'], boundry['east'], boundry['south'], boundry['north']
    ])
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
        print(dir_name)
        if not os.path.exists(file_dist):
            os.makedirs(file_dist)
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.snappy'):
                continue
            trajectories = modify_data(os.path.join(file_path, dir_name, file), boundry)
            file_name = file_dist + '/' + prefix + '-' + file.split('.snappy')[0]+'.csv'
            with open(file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                for trajectory in trajectories:
                    if trajectory[1]:
                        for point in trajectory[1]:
                            writer.writerow([trajectory[0]]+point)
    return trajectories


def make_traj_matrix(trajs):
    trajectories = []
    for traj in trajs:
        if traj[1]:
            new_traj = LineString([(point[0], point[1]) for point in traj[1]])
            trajectories.append((traj[0], new_traj))
    return trajectories


