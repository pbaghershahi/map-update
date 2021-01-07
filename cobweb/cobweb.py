import numpy as np
import geopandas as gp
from scipy.spatial.distance import cdist
from collections import deque
import pandas as pd
import pickle

def geo_center(S, vertices):
    S = list(S)
    mean_point = np.mean(vertices[S], axis=0)
    dists = np.linalg.norm(vertices[S]-mean_point, axis=1)
    center = S[np.argmin(dists)]
    return center

def adjacent_vertex(S, adjacencies):
    out_vertices = set()
    for p in S:
        adjacents = set(np.where(adjacencies[p]==1)[0])
        complements = adjacents-S
        out_vertices = out_vertices.union(complements)
    return out_vertices

def compute_dist(point, seed, dists, predecessors):
    cobweb_dist = 0
    predecessor = predecessors[point]
    while point != seed:
        cobweb_dist += dists[point, predecessor]
        point = predecessor
        predecessor = predecessors[point]
    return cobweb_dist


def gen_cobweb(traj_file, Rv=0.00015, Rc=0.0009, Pv=10, Pc=10, unmatch=True, match_file='./matches.csv'):
    # trajectories = gp.read_file(traj_file)
    # trajectories.set_index('id', drop=True, inplace=True)
    trajectories = gp.read_file(traj_file)
    if unmatch:
        matches = pd.read_csv(match_file, sep=';', index_col='id', engine='python')
        matches = matches[matches.cpath.isnull()]
        # trajectories = trajectories[trajectories.index.isin(matches.index)]
        trajectories = trajectories[trajectories.id.isin(matches.index)]
        trajectories.reset_index(drop=True, inplace=True)
    bearing_lens = trajectories['bearing'].apply(lambda x: len(x.split(',')))
    coords_lens = trajectories['geometry'].apply(lambda x: np.array(x.coords).shape[0])
    mis_aligns = np.where((bearing_lens == coords_lens) == False)[0]
    trajectories = trajectories.drop(mis_aligns, axis=0)
    trajectories.set_index('id', drop=True, inplace=True)
    bearings = np.concatenate(np.array(trajectories['bearing'].apply(lambda x: np.array(x.split(',')).astype(np.float))))
    newarray = np.concatenate(np.array(trajectories['geometry'].apply(lambda x: np.array(x.coords))))
    total_nodes = newarray.shape[0]
    V_set = []
    B_set = []
    while newarray.size > 0:
        # rand_point = newarray[np.random.choice(newarray.shape[0], size=1, replace=False)][0]
        # V_set.append(rand_point)
        # dists = np.linalg.norm(newarray-rand_point, axis=1)
        # newarray = newarray[dists>Rv]
        rand_index = np.random.choice(newarray.shape[0], size=1, replace=False)
        rand_point, rand_bearing = newarray[rand_index][0], bearings[rand_index][0]
        V_set.append(rand_point)
        B_set.append(rand_bearing)
        dists = np.linalg.norm(newarray - rand_point, axis=1)
        angle_diffs = abs(bearings - rand_bearing)
        unmerge = (dists > Rv) | (angle_diffs > Pv)
        newarray = newarray[unmerge]
        bearings = bearings[unmerge]
    V_set = np.vstack(V_set)
    dists = cdist(V_set, V_set)
    B_set = np.array([B_set] * len(B_set))
    adiffs = abs(B_set - B_set.T)
    # adj_matrix = np.ma.getmask(np.ma.masked_where(dists<Rc, dists)).astype(np.int)
    adj_matrix = ((dists < Rc)*(adiffs < Pc)).astype(np.int)
    np.fill_diagonal(adj_matrix, 0)

    return V_set, adj_matrix, dists, total_nodes


def from_roadTree(V_set, adj_matrix, dists, r=0.0010, delta=6, save_graphPath='./graph.pkl'):
    indices = np.arange(0, V_set.shape[0], 1)
    all_marked = set()
    all_nodes = set(range(V_set.shape[0]))
    random_choices = []

    while all_nodes != all_marked:
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


        graph_dict = {'marks':marks, 'S':S, 'graph_adj':adj_matrix, 'indices':indices, 'seed':V_set[s]}
        with open(save_graphPath, 'wb') as graph_file:
            pickle.dump(graph_dict, graph_file)
        # sleep(2)

        marks[s] = 1
        S.add(s)
        print(f'set S is: {S}')

        while len(Q_g) != 0:
            predecessors = {}
            print(f'Q_g currently is: {Q_g}')
            print(f'Q_l currently is: {Q_l}')
            seed = Q_g.pop()
            predecessors[seed] = seed
            print(f'node {seed} choosed as seed')
            print(f'adjacent nodes to seed {seed} are {np.where(adj_matrix[seed]==1)[0]}')
            for p in np.where(adj_matrix[seed]==1)[0]:
                if marks[p] != 1:
                    print(f'node {p} accepted as adjacent to seed {seed} and it is unmarked')
                    marks[p] = 1
                    Q_l.appendleft(p)
                    print(f'node {p} marked and appended to Q_l')
                    predecessors[p] = seed
                    # distances.appendleft(dists[p, seed])
                    distances.appendleft(compute_dist(p, seed, dists, predecessors))
                else:
                    print(f'node {p} accepted as adjacent to seed {seed} but it is marked')
            print(f'adjcent nodes to seed {seed} all appended to Q_l. Now Q_l is : {Q_l}')
            while len(Q_l) != 0:
                p = Q_l.pop()
                print(f'node {p} poped from Q_l')
                temp_dist = distances.pop()
                if temp_dist < r:
                    print(f'distance from node {p} to seed {seed} is: {temp_dist} below the threshold {r}')
                    count += 1
                    S.add(p)
                    print(f'node {p} added to set S. Now S is: {S}')
                    print(f'adjacent nodes to {p} are {np.where(adj_matrix[p]==1)[0]}')
                    for p_prime in np.where(adj_matrix[p]==1)[0]:
                        if marks[p_prime] != 1:
                            print(f'node {p_prime} accepted as adjacent to {p} and it is unmarked')
                            marks[p_prime] = 1
                            Q_l.appendleft(p_prime)
                            print(f'node {p_prime} marked and appended to Q_l')
                            # distances.appendleft(dists[p_prime, seed])
                            predecessors[p_prime] = p
                            distances.appendleft(compute_dist(p_prime, seed, dists, predecessors))
                        else:
                            print(f'node {p_prime} accepted as adjacent to {p} but it is marked')
                    print(f'adjcent nodes to {p} all appended to Q_l. Now Q_l is : {Q_l}')

                    graph_dict = {'marks':marks, 'S':S, 'graph_adj':adj_matrix, 'indices':indices, 'seed':V_set[seed]}
                    with open(save_graphPath, 'wb') as graph_file:
                        pickle.dump(graph_dict, graph_file)
                    # sleep(0.5)

                else:
                    print(f'distance from node {p} to seed {seed} is: {temp_dist} above the threshold {r}')
                    if count > delta:
                        print(f'number of nodes in S are: {count} above the threshold {delta}')
                        Vc = geo_center(S, V_set)
                        print(f'node {Vc} choosed as the geocenter node')
                        V_prime = adjacent_vertex(S, adj_matrix)
                        print(f'nodes {V_prime} are out of S')
                        ommited = list(S-{Vc})
                        print(f'nodes {ommited} ommited from V except geocenter {Vc}')
                        indices = indices[~np.isin(indices, ommited)]
                        adj_matrix[:, ommited] = 0
                        adj_matrix[ommited] = 0
                        for v in V_prime:
                            Q_g.appendleft(v)
                            print(f'node {v} from V_prime appended to Q_g')
                            adj_matrix[v, Vc] = 1
                            adj_matrix[Vc, v] = 1
                        count = 0
                        S = set()
                        print('set S got empty')
                    else:
                        print(f'number of nodes in S are: {count} below the threshold {delta}')

                    graph_dict = {'marks':marks, 'S':S, 'graph_adj':adj_matrix, 'indices':indices, 'seed':V_set[seed]}
                    with open(save_graphPath, 'wb') as graph_file:
                        pickle.dump(graph_dict, graph_file)
                    # sleep(0.5)

                    # eddited on the original algorithm
                    all_marked = all_marked.union(set(np.where(marks==1)[0]))
                    while len(Q_l) != 0:
                        p = Q_l.pop()
                        print(f'node {p} poped from Q_l and unmarked')
                        marks[p] = 0
                    distances.clear()

                all_marked = all_marked.union(set(np.where(marks==1)[0]))
                print('*'*50)

            # eddited on the original algorithm
            count = 0
            S = set()

    all_marked = all_marked.union(set(np.where(marks==1)[0]))
    print(f'{"="*60} all marked are: {all_marked}')
    print(f'{"="*60} all nodes: {all_nodes}')
    print(f'{"="*60} random choices for s: {random_choices}')

    return adj_matrix


if __name__=='__main__':
    np.random.seed(123456)
    traj_file = './data-test/trajectories/trajs.shp'
    match_file = './data-test/mr.csv'
    unmatch = True
    Rv = 0.00015
    Rc = 0.0009
    V_set, adj_matrix, dists, _ = gen_cobweb(traj_file, Rv, Rc, unmatch, match_file)
    r = 0.0010
    delta = 6
    save_graphPath = '/home/peyman/Documents/projects/balad/codes/test/graph.pkl'
    adj_matrix = from_roadTree(V_set, adj_matrix, dists, r, delta, save_graphPath)