import geopandas as gp
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import numpy as np

# matches = pd.read_csv('./data/mr.csv', sep=';', index_col='id', engine='python')
# print(matches)
# matches = matches[matches.cpath.notnull()]
# matches = matches[matches.cpath.isnull()]
# print(matches)
# filtered_edges = gp.read_file('./ground-map/map/filtered_edges.shp')
# filtered_edges.set_index('id', drop=True, inplace=True)
# all_edges = gp.read_file('./ground-map/map/all_edges.shp')
# all_edges.set_index('id', drop=True, inplace=True)
# trajectories = gp.read_file('./data/trajectories/trajs.shp')
# trajectories.set_index('id', drop=True, inplace=True)
# trajectories = trajectories[trajectories.index.isin(matches.index)]

# all_edges.plot()
# filtered_edges.plot()
#
# for index, row in trajectories.iterrows():
#     try:
#         traj = trajectories.loc[index]['geometry']
#         a = np.array(traj.coords)[:, 0]
#         b = np.array(traj.coords)[:, 1]
#         plt.plot(a, b, 'r')
#     except:
#         for row in traj:
#             a = np.array(row.coords)[:, 0]
#             b = np.array(row.coords)[:, 1]
#             plt.plot(a, b, 'r')
#         continue


# for index, row in trajectories.iterrows():
#     try:
#         if index in [25600, 31750, 30221, 12305, 7190, 35864, 34845, 28195, 30246, 28199, 33327, 5682, 9274, 27716, 9799, 33352, 9292, 34908, 17506, 31330, 29287, 33390, 25712, 30321, 31358, 36482, 13956, 10886, 19593, 34441, 22160, 7828, 31391, 30881, 33449, 9898, 24751, 26800, 36016, 20658, 36542, 25819, 36573, 32480, 32481, 36069, 36070, 33002, 13552, 35057, 25341, 27904, 33536, 26882, 32006, 32518, 36104, 34057, 32016, 36117, 26403, 35622, 32559, 19767, 35641, 26938, 30024, 35658, 27979, 35148, 26962, 29553, 30581, 32117, 35191, 35206, 35210, 34190, 24986, 35739, 35740, 21917, 28063, 36256, 14753, 18344, 22952, 34225, 34227, 29624, 35773, 32705, 33223, 35280, 35282, 31189, 33244, 21989, 33779, 33273]:
#             print('here')
#             traj = trajectories.loc[index]['geometry']
#             a = np.array(traj.coords)[:, 0]
#             b = np.array(traj.coords)[:, 1]
#             plt.plot(a, b, 'r')
#     except:
#         for row in traj:
#             a = np.array(row.coords)[:, 0]
#             b = np.array(row.coords)[:, 1]
#             plt.plot(a, b, 'r')
#         continue



# ploted_filtered_edges = []
#
# for index, row in matches.iterrows():
#     edge_ids = row['cpath'].split(',')
#     try:
#         traj = trajectories.loc[index]['geometry']
#         a = np.array(traj.coords)[:, 0]
#         b = np.array(traj.coords)[:, 1]
#         plt.plot(a, b, 'r')
#     except:
#         continue
#     for edge_id in edge_ids:
#         if edge_id in ploted_filtered_edges:
#             continue
#         ploted_filtered_edges.append(edge_id)
#         edge = filtered_edges.loc[int(edge_id)]['geometry']
#         # edge = all_edges.loc[int(edge_id)]['geometry']
#         a = np.array(edge.coords)[:, 0]
#         b = np.array(edge.coords)[:, 1]
#         plt.plot(a, b, c='k')


# plt.savefig('matches.png')


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