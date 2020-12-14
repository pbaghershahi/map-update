from matplotlib.animation import FuncAnimation
import pickle
import numpy as np
import matplotlib.pyplot as plt
from cobweb import gen_cobweb
import networkx as nx


def animate(i):
    with open('/home/peyman/Documents/projects/balad/codes/test/graph.pkl', 'rb') as graph_file:
        graph_dict = pickle.load(graph_file)

    marks = graph_dict['marks']
    S = graph_dict['S']
    G = nx.from_numpy_array(graph_dict['graph_adj'])
    indices = graph_dict['indices']
    unmarked_labels = {i:str(i) for i in indices}
    marked_labels = {i:str(i) for i in np.where(marks == 1)[0]}
    s_labels = {i:str(i) for i in list(S)}
    plt.cla()
    # plt.tight_layout()
    print(f'marked nodes: {np.where(marks == 1)[0]}')
    print(f'unmarked nodes: {np.where(marks == 0)[0]}')
    print(f'set S: {list(S)}')
    print('*'*50)
    # nx.draw_networkx(G, pos, nodelist=np.where(marks == 0)[0], node_color="b", **options)
    nx.draw_networkx(G, pos, nodelist=indices, node_color="b", labels=unmarked_labels, **options)
    nx.draw_networkx(G, pos, nodelist=np.where(marks == 1)[0], labels=marked_labels, node_color="r", **options)
    nx.draw_networkx(G, pos, nodelist=list(S), node_color="g", labels=s_labels, **options)
    plt.text(51.3497, 35.7414, f'Number of current nodes:\n {len(indices)} out of {total_nodes}', fontsize=8, color='g')


if __name__ == '__main__':
    np.random.seed(123456)
    traj_file = './data-test/trajectories/trajs.shp'
    Rv = 0.00015
    Rc = 0.0009
    V_set, adj_matrix, dists, total_nodes = gen_cobweb(traj_file, Rv, Rc)
    G = nx.from_numpy_array(adj_matrix)
    fixed_positions = dict(zip(np.arange(0, V_set.shape[0], 1), V_set))
    pos = nx.spring_layout(G, pos=fixed_positions, fixed=G.nodes())
    options = {"node_size": 50, "font_size": 10, "alpha": 0.8, "with_labels": True}
    plt.style.use('fivethirtyeight')
    ani = FuncAnimation(plt.gcf(), animate, interval=1000)

    plt.tight_layout()
    plt.show()
