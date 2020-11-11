import geopandas as gp
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import numpy as np

matches = pd.read_csv('./data/mr.csv', sep='\;')
edges = gp.read_file('./ground-map/map/edges.shp')
trajectories = gp.read_file('./data/trajectories/trajs.shp')

edges.plot()
ploted_edges = []
for i in range(len(matches)):
    edge_ids = matches.iloc[i]['cpath'].split(',')
    for edge_id in edge_ids:
        if edge_id in ploted_edges:
            continue
        ploted_edges.append(edge_id)
        edge = edges[(edges['id']==int(edge_id))]['geometry'].iloc[0]
        a = np.array(edge.coords)[:, 0]
        b = np.array(edge.coords)[:, 1]
        plt.plot(a, b, c='k')

for i in range(len(trajectories)):
    traj = trajectories['geometry'].iloc[i]
    a = np.array(traj.coords)[:, 0]
    b = np.array(traj.coords)[:, 1]
    plt.plot(a, b)

plt.savefig('matches.png')
plt.show()