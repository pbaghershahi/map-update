import numpy as np
import geopandas as gp
from scipy.spatial.distance import cdist
import pickle
from cobweb import gen_cobweb

if __name__=='__main__':
    np.random.seed(123456)
    traj_file = './data-test/trajectories/trajs.shp'
    match_file = './data-test/mr.csv'
    unmatch = True
    Rv = 0.0001
    Rc = 0.00095
    Pv = 10
    Pc = 45
    V_set, adj_matrix, dists, total_nodes = gen_cobweb(traj_file, Rv, Rc, Pv, Pc, unmatch, match_file)
    indices = np.arange(0, V_set.shape[0], 1)
    random_choices = []
    s = np.random.choice(indices[~np.isin(indices, random_choices)])
    S = set()
    marks = np.zeros((V_set.shape[0]), np.int)
    graph_dict = {'marks':marks, 'S':S, 'graph_adj':adj_matrix, 'indices':indices, 'seed':V_set[s]}
    with open('/home/peyman/Documents/projects/balad/codes/test/graph.pkl', 'wb') as graph_file:
        pickle.dump(graph_dict, graph_file)