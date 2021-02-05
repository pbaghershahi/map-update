import geopandas as gp
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import numpy as np

# matches = pd.read_csv('./test/data-test/mr.csv', sep=';', index_col='id', engine='python')
# # matches = matches[matches.cpath.notnull()]
# matches = matches[matches.cpath.isnull()]
# filtered_edges = gp.read_file('./ground-map/map/filtered_edges.shp')
# filtered_edges.set_index('id', drop=True, inplace=True)
# all_edges = gp.read_file('./ground-map/map/all_edges.shp')
# all_edges.set_index('id', drop=True, inplace=True)
trajectories = gp.read_file('./data/trajectories/trajs.shp')
trajectories.set_index('id', drop=True, inplace=True)
# trajectories = trajectories[trajectories.index.isin(matches.index)]

# all_edges.plot()
# filtered_edges.plot()
#
for index, row in trajectories.iterrows():
    try:
        traj = trajectories.loc[index]['geometry']
        a = np.array(traj.coords)[:, 0]
        b = np.array(traj.coords)[:, 1]
        plt.plot(a, b, 'r')
    except:
        # for row in traj:
        #     a = np.array(row.coords)[:, 0]
        #     b = np.array(row.coords)[:, 1]
        #     plt.plot(a, b, 'r')
        continue

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
#         a = np.array(edge.coords)[:, 0]
#         b = np.array(edge.coords)[:, 1]
#         plt.plot(a, b, c='k')


plt.savefig('matches.png')
plt.show()