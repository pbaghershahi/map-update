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

def insert_nodes(node1, node2, n):
    latitudes = np.linspace(node1[0], node2[0], n)
    longitudes = np.linspace(node1[1], node2[1], n)
    nodes = list(zip(longitudes, latitudes))
    return nodes

def convert_location(x):
    point = wkb.loads(x, hex=True)
    return point.x, point.y

def edgeToShape(map_dbpath, dist_path, min_length=20, n=5, without_postprocess=True):
    con = sqlite3.connect(map_dbpath)
    edges_df = pd.read_sql_query("SELECT id, in_node, out_node, weight FROM edges", con)
    nodes_df = pd.read_sql_query("SELECT id, latitude, longitude, weight FROM nodes", con)
    nodes_df.set_index('id', drop=True, inplace=True)
    # find the start and end nodes coordinates for each edge of the edges table
    # based on nodes of the nodes table
    # filter edges by minimum length
    if without_postprocess:
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

# f'python edge_traj.py --map_dbpath {results_path}/skeleton-maps/skeleton_map_1m.db --shape_output_path {inference_path}/edges.shp --n_edge_splits 9 --min_length {min_length}')
edgeToShape('./skeleton_map_2m.db', './test/before_edges.shp', 20, 9)
print('*'*60)
edgeToShape('./skeleton_map_3m.db', './test/after_edges.shp', 20, 9)

before_edges = gp.read_file('./test/before_edges.shp')
after_edges = gp.read_file('./test/after_edges.shp')
filtered_map = gp.read_file('./ground-map/map/dropped_edges.shp')
# filtered_map = gp.read_file('./ground-map/map/all_edges.shp')
# filtered_map = gp.read_file('./ground-map/map/filtered_edges.shp')

import matplotlib.pyplot as plt

# before_edges.plot()
# plt.title('before')
# after_edges.plot()
# plt.title('after')


filtered_map.plot()
# plt.title('CG')
counter = 0
for index, row in before_edges.iterrows():
    coords = list(row.geometry.coords)
    if counter == len(before_edges) - 1:
        plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r', label='detected edges')
    else:
        plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')
    counter += 1
plt.title('before')


# a = [12, 58, 66, 68, 90, 94, 132, 138, 142, 166, 168, 176, 200, 206, 220, 224, 226, 242, 256, 262, 272, 280, 298, 304, 312, 352, 356, 384, 392, 412, 448, 460, 474, 486, 488, 516, 518, 524]
a = [142]
filtered_map.plot()
counter = 0
for index, row in after_edges.iterrows():
    # if row.pre_id in a:
    #     coords = list(row.geometry.coords)
    #     if counter == len(after_edges) - 1:
    #         plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r', label='detected edges')
    #     else:
    #         plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')
    # else:
    #     coords = list(row.geometry.coords)
    #     if counter == len(after_edges) - 1:
    #         plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='g', label='detected edges')
    #     else:
    #         plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='g')
    coords = list(row.geometry.coords)
    if counter == len(after_edges) - 1:
        plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r', label='detected edges')
    else:
        plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')
    counter += 1
plt.title('after')

plt.show()