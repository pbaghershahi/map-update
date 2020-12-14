import pandas as pd
import numpy as np
import osmnx as ox
import datetime
import seaborn as sn
from shapely import wkb
from shapely.geometry import Point
from shapely.geometry import LineString
import geopandas as gp
import matplotlib.pyplot as plt
import hashlib
from scipy.spatial.distance import cdist
import os
from collections import deque
import networkx as nx
from time import sleep
from copy import deepcopy
from sympy import Matrix, init_printing
import pickle

def geo_center(S, vertices):
    S = list(S)
    mean_point = np.mean(vertices[S], axis=0)
    dists = np.linalg.norm(vertices[S]-mean_point, axis=1)
#     print(f'arg min to geocenter: {np.argmin(dists)}')
    center = S[np.argmin(dists)]
    return center

def adjacent_vertex(S, adjacencies):
    out_vertices = set()
    for p in S:
        adjacents = set(np.where(adjacencies[p]==1)[0])
        complements = adjacents-S
        out_vertices = out_vertices.union(complements)
    return out_vertices

trajectories = gp.read_file('./data-test/trajectories/trajs.shp')
trajectories.set_index('id', drop=True, inplace=True)

np.random.seed(123456)
newarray = np.concatenate(np.array(trajectories['geometry'].apply(lambda x: np.array(x.coords))))
Rv = 0.00015
V_set = []
while newarray.size > 0:
    rand_point = newarray[np.random.choice(newarray.shape[0], size=1, replace=False)][0]
    V_set.append(rand_point)
    dists = np.linalg.norm(newarray-rand_point, axis=1)
    newarray = newarray[dists>Rv]
V_set = np.vstack(V_set)

Rc = 0.0009
dists = cdist(V_set, V_set)
adj_matrix = np.ma.getmask(np.ma.masked_where(dists<Rc, dists)).astype(np.int)
np.fill_diagonal(adj_matrix, 0)



r = 0.0010
delta = 6
indices = np.arange(0, V_set.shape[0], 1)
all_marked = set()
all_nodes = set(range(V_set.shape[0]))
random_choices = []

s = np.random.choice(indices[~np.isin(indices, random_choices)])
random_choices.append(s)
Q_g = deque()
Q_g.appendleft(s)
Q_l = deque()
# eddited on the original algorithm
Q_l.appendleft(s)
distances = deque()
distances.appendleft(0)
count = 0
S = set()
marks = np.zeros((V_set.shape[0]), np.int)


graph_dict = {'marks':marks, 'S':S, 'graph_adj':adj_matrix, 'indices':indices}
with open('/home/peyman/Documents/projects/balad/codes/test/graph.pkl', 'wb') as graph_file:
    pickle.dump(graph_dict, graph_file)
