import geopandas as gp
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import numpy as np

matches = pd.read_csv('./data-test/mr.csv', sep=';', index_col='id', engine='python')
matches = matches[matches.cpath.notnull()]
# matches = matches[matches.cpath.isnull()]
edges = gp.read_file('./ground-map/map/edges.shp')
edges.set_index('id', drop=True, inplace=True)
trajectories = gp.read_file('./data-test/trajectories/trajs.shp')
trajectories.set_index('id', drop=True, inplace=True)


edges.plot()

# for i in range(len(trajectories)):
#     traj = trajectories['geometry'].iloc[i]
#     a = np.array(traj.coords)[:, 0]
#     b = np.array(traj.coords)[:, 1]
#     plt.plot(a, b, 'y')

ploted_edges = []

for index, row in matches.iterrows():
    edge_ids = row['cpath'].split(',')
    # if index != 473449167:
    #     continue
    # edge_ids = row['opath'].split(',')
    try:
        traj = trajectories.loc[index]['geometry']
        a = np.array(traj.coords)[:, 0]
        b = np.array(traj.coords)[:, 1]
        plt.plot(a, b, 'r')
    except:
        continue
    for edge_id in edge_ids:
        # if edge_id != '259':
        #     continue
        if edge_id in ploted_edges:
            continue
        ploted_edges.append(edge_id)
        edge = edges.loc[int(edge_id)]['geometry']
        a = np.array(edge.coords)[:, 0]
        b = np.array(edge.coords)[:, 1]
        plt.plot(a, b, c='k')
        # plt.plot(a, b)


plt.savefig('matches.png')
plt.show()