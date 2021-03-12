import pandas as pd
import geopandas as gp
import matplotlib.pyplot as plt

matches = pd.read_csv('./data/mr.csv', sep=';', index_col='id', engine='python')
edges = gp.read_file('./data/edges.shp')
edges.set_index('id', drop=True, inplace=True)

unmatched_indices = matches[matches.unmatch == True].index
unmatched_edges = edges.loc[unmatched_indices]
filtered_edges = gp.read_file('./ground-map/map/filtered_edges.shp')
filtered_edges.set_index('id', drop=True, inplace=True)
filtered_edges.plot()

for index, row in unmatched_edges.iterrows():
    coords = list(row.geometry.coords)
    plt.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')

# filtered_edges.plot()
# all_edges = gp.read_file('./ground-map/map/all_edges.shp')
# all_edges.set_index('id', drop=True, inplace=True)
# all_edges.plot()

# id = 30
# matched_edges = [int(x) for x in matches.loc[id].cpath.split(',')]
# lats = []
# lons = []
# for edge_id in range(len(matched_edges)):
#     edge = list(filtered_edges.loc[matched_edges[edge_id]].geometry.coords)
#     for node in edge:
#         lons.append(node[0])
#         lats.append(node[1])
#     plt.plot(lons, lats, 'r*')
#     lats = []
#     lons = []
#
# matched_edges = [int(x) for x in matches.loc[id].opath.split(',')]
# lats = []
# lons = []
# for edge_id in range(len(matched_edges)):
#     edge = list(filtered_edges.loc[matched_edges[edge_id]].geometry.coords)
#     for node in edge:
#         # print(node[0], node[1])
#         lons.append(node[0])
#         lats.append(node[1])
#     if matched_edges[edge_id] == 1067:
#         plt.plot(lons, lats, c='c')
#         continue
#     plt.plot(lons, lats, c='k')
#     lats = []
#     lons = []
#
# lats = []
# lons = []
# sample_edge = list(edges.loc[id].geometry.coords)
#
# for node in sample_edge:
#     lons.append(node[0])
#     lats.append(node[1])
# plt.plot(lons, lats, c='g')

plt.show()