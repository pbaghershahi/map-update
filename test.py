import pandas as pd
import numpy as np
import osmnx as ox
from shapely import wkb
import matplotlib.pyplot as plt
import datetime
import os, csv


def modify_data(file_path, boundary):
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
            trajectories.append(sorted(temp_point, key=lambda x: x[2]))
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
    for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(x) and not x.startswith('.')]:
        new_dir = os.path.join(file_dist, dir_name)
        print(new_dir)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        files = sorted(os.listdir(os.path.join(file_path, dir_name)))
        for file in files:
            if not file.endswith('.snappy'):
                continue
            print(file)
            trajectories = modify_data(os.path.join(file_path, dir_name, file), boundry)
            file_name = new_dir + '/' + prefix + '-' + file.split('.snappy')[0]+'.csv'
            print(file_name)
            with open(file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                for trajectory in trajectories:
                    for point in trajectory:
                        writer.writerow(point)
    return trajectories


north = 35.7417
south = 35.7340
east = 51.3520
west = 51.3430
# graph = ox.graph_from_bbox(north, south, east, west, network_type='drive')
# area = ox.geometries_from_bbox(north, south, east, west, tags={'highway':True})
# area.plot()

# sample_file = "part-00002-498c167d-fb29-4098-a9f9-682631b98b93-c000.snappy"
# modified_data = modified_data(sample_file)
files_path = './'
boundry = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
_ = load_data(files_path, boundry, './')
# modified_data = modify_data(sample_file, boundry)
#
# for i in range(len(modified_data)):
#     plt.plot([modified_data[i][j][0] for j in range(len(modified_data[i]))],
#              [modified_data[i][j][1] for j in range(len(modified_data[i]))], c='red')
#
# plt.show()


