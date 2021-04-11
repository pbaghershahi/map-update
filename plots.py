import geopandas as gp
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import pandas as pd
from haversine import haversine, Unit

import osmnx as ox
import numpy as np


matches = pd.read_csv('./data/mr.csv', sep=';', index_col='id', engine='python')
trajs_matches = pd.read_csv('./data/trajs_mr.csv', sep=';', index_col='id', engine='python')
trajs_matches = trajs_matches[trajs_matches.cpath.notna()]
edges = gp.read_file('./data/inferred-edges/edges.shp')
edges.set_index('id', drop=True, inplace=True)

unmatched_indices = matches[matches.unmatch==True].index
unmatched_edges = edges[edges.index.isin(unmatched_indices)]

print(edges[edges.way_length<20])

# filtered_edges = gp.read_file('./ground-map/map/filtered_edges.shp')
# filtered_edges.set_index('id', drop=True, inplace=True)
# filtered_edges.plot()

dropped_edges = gp.read_file('./ground-map/map/dropped_edges.shp')
dropped_edges.set_index('id', drop=True, inplace=True)
dropped_edges = dropped_edges[dropped_edges.way_length > 20]

dropped_edges['num_trips'] = 0
for match_idx, row in trajs_matches.iterrows():
    for edge_idx in [int(k) for k in row.cpath.split(',')]:
        if edge_idx in dropped_edges.index:
            dropped_edges.num_trips.loc[edge_idx] += 1
dropped_edges = dropped_edges[dropped_edges.num_trips >= 1]

dropped_edges.plot()

for index, row in unmatched_edges.iterrows():
    coords = list(row.geometry.coords)
    plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')


plt.show()