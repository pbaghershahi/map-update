import pandas as pd
import numpy as np
import geopandas as gp
from copy import deepcopy
import sqlite3
from spatialfunclib import haversine_distance, point_along_line
import argparse



class Node:
    def __init__(self, node_id, latitude, longitude):
        self.id = node_id
        self.coordinates = (latitude, longitude)
        self.edges = set()
        self.neighbors = set()

# returns index of the nearest node of an array to a given node.
def distance_argmin(nodes, sample_node):
    distances = []
    for i in range(len(nodes)):
        distances.append(haversine_distance(nodes[i], sample_node))
    return np.argmin(distances)

# stick edges to each other based on the common edges between nodes
def stick_edge(point_edge_list):
    big_edges = {}
    while len(point_edge_list) > 0:
        point_key, edge_ids = point_edge_list.popitem()
        edge_ids = list(edge_ids)
        # for nodes with common edges union the the other nodes have the same shred edge
        for edge_id in edge_ids:
            for point, edges in point_edge_list.copy().items():
                if edge_id in edges:
                    _ = point_edge_list.pop(point)
                    edge_ids += list(edges.difference(set(edge_ids)))
        big_edges[point_key] = set(edge_ids)
    return big_edges

# generate a dictionary of nodes which has node ids and keys and Node objects as values
def generate_node_mapping(coords_geoms):
    # first create a dictionary with nodes coordinates as keys and Nodes objects as values
    # store the edges which each node is shared between them
    nodes_str_mapping = {}
    id_counter = 0
    for index, item in coords_geoms.iteritems():
        for i in range(item.shape[0]):
            node_key = f'({item[i][0]},{item[i][1]})'
            if node_key not in nodes_str_mapping.keys():
                nodes_str_mapping[node_key] = Node(id_counter, *item[i])
                nodes_str_mapping[node_key].edges.add(index)
                id_counter += 1
            else:
                nodes_str_mapping[node_key].edges.add(index)

    # replace the coordinate keys with node ids and store each node neighbors in it
    nodes_mapping = {}
    for index, item in coords_geoms.iteritems():
        for i in range(item.shape[0]):
            node_key = f'({item[i][0]},{item[i][1]})'
            node_id = nodes_str_mapping[node_key].id
            nodes_mapping[node_id] = nodes_str_mapping[node_key]
            nodes_mapping[node_id].neighbors.add(
                nodes_str_mapping[f'({item[int(not i)][0]},{item[int(not i)][1]})'].id
            )
    return nodes_mapping

# recursively generate virtual nodes (e.g. holes and marbles) between
# each pair of neighboring nodes and store them in a list
def recursive_node_generation(nodes_mapping, r, d, init_node_id, nodes, traveled_distance):
    init_node = nodes_mapping[init_node_id]
    for neighbor_id in init_node.neighbors.copy():
        # use haversine distance to consider exact distance on earth in meters and taking
        # care of latitude and longitude difference in meters per unit
        distance = haversine_distance(init_node.coordinates, nodes_mapping[neighbor_id].coordinates)
        # for each neighbor of the initial node check the distance condition and if
        # it was bigger than specific distance d break the distance and generate
        # virtual nodes in between until passing the distance threshold
        if distance > d and traveled_distance + d < r:
            node_coordinates = point_along_line(
                *init_node.coordinates, *nodes_mapping[neighbor_id].coordinates, d/distance
            )
            new_id = len(nodes_mapping)
            nodes.append(node_coordinates)
            nodes_mapping[new_id] = Node(new_id, *node_coordinates)
            # remove neighbor node from the initial node neighbors and vice versa,
            # but just add the neighbor node to the newly generated node because
            # we are recursively breaking the distance between current nodes and
            # the unseen nodes not the visited ones
            nodes_mapping[new_id].neighbors.add(neighbor_id)
            nodes_mapping[init_node_id].neighbors.discard(neighbor_id)
            nodes_mapping[neighbor_id].neighbors.discard(init_node_id)
            recursive_node_generation(nodes_mapping, r, d, new_id, nodes, traveled_distance + d)
        # if the distance between the neighbor node and the initial node
        # is smaller than the specific distance d, just add and store
        # the neighbor id in the newly added nodes list
        elif distance < d and traveled_distance + distance < r:
            nodes.append(nodes_mapping[neighbor_id].coordinates)
            nodes_mapping[neighbor_id].neighbors.discard(init_node_id)
            recursive_node_generation(nodes_mapping, r, d, neighbor_id, nodes, traveled_distance + distance)

# generate holes and marbles simultaneously and store them in a dict
def generate_nodes(gt_nodes_mapping, pr_nodes_mapping, r, d, check_threshold):
    initial_mapping_len = len(gt_nodes_mapping)
    num_checked_nodes = 0
    # fixme: change the break out condition
    new_nodes = {'holes': set(), 'marbles': set()}
    while num_checked_nodes / initial_mapping_len < check_threshold:
        itr_dict = {'holes': gt_nodes_mapping, 'marbles': pr_nodes_mapping}
        temp_gen_nodes = {'holes': [], 'marbles': []}
        for key, nodes_mapping in itr_dict.items():
            # iteratively choose a new random node as a seed and generate
            # holes or marbles close to it limited to an specific distance r
            traveled_dist = 0
            if key == 'holes':
                random_node_id = np.random.choice(np.array(list(nodes_mapping.keys())), 1)[0]
                # store the current holes_mapping for the next iteration of creating
                # marbles because the holes_mapping get change in each iteration
                random_hole_id, last_gt_mappings = random_node_id, deepcopy(nodes_mapping)
                num_checked_nodes += len(nodes_mapping[random_node_id].neighbors) + 1
            else:
                pr_nodes = list(nodes_mapping.values())
                pr_nodes_coords = np.array([node.coordinates for node in pr_nodes])
                try:
                    # find the node closet to the initial hole to put the initial marble just as explained by Biagioni
                    random_node_id = pr_nodes[
                        distance_argmin(pr_nodes_coords, last_gt_mappings[random_hole_id].coordinates)].id
                except:
                    print(f'Warnnings!\nThere are not not enough predicted nodes on map to check'
                          f' more at least {check_threshold * 100}% of ground truth nodes.')
                    return ""
            temp_gen_nodes[key].append(nodes_mapping[random_node_id].coordinates)
            recursive_node_generation(deepcopy(nodes_mapping), r, d, random_node_id, temp_gen_nodes[key], traveled_dist)
            # remove the last random node choice from the nodes_mapping
            # to avoid mis-operations and more complexity.
            # Also remove its connections to its neighbors
            random_nbr_ids = nodes_mapping.pop(random_node_id).neighbors
            for neighbor_id in random_nbr_ids:
                nodes_mapping[neighbor_id].neighbors.discard(random_node_id)
            # union the holes and marbles with the last generated set of them to avoid duplications
            new_nodes[key] = new_nodes[key].union(set(temp_gen_nodes[key]))
    for key, value in new_nodes.items():
        new_nodes[key] = list(value)
    return new_nodes

# match each hole and marble with their nearest marble and hole
def match_hole_marble(generated_nodes, error_threshold):
    MAX_VALUE = 1e05
    distances = np.zeros((len(generated_nodes['marbles']), len(generated_nodes['holes'])))
    # compute the haversine distance between each hole and marble
    for i in range(distances.shape[0]):
        for j in range(distances.shape[1]):
            distances[i, j] = haversine_distance(generated_nodes['marbles'][i], generated_nodes['holes'][j])
    matches = []
    for i in range(distances.shape[0]):
        nearest_hole_index = np.argmin(distances[i])
        for j in range(distances.shape[1]):
            nearest_marble_index = np.argmin(distances[:, j])
            # check if just both the hole and the marble are the closets ones to each other,
            # add them to the matched pairs not just one of the conditions satisfied
            if nearest_hole_index == j and nearest_marble_index == i:
                if distances[i, j] <= error_threshold:
                    matches.append((i, j))
                # fill the matched rows and columns with a big number
                # to take them out of consideration for the other comparisons
                distances[i] = MAX_VALUE
                distances[:, j] = MAX_VALUE
    return matches, distances

# evaluate precision, recall, f_score
def evalute_prf(generated_nodes, error_threshold):
    matches, _ = match_hole_marble(generated_nodes, error_threshold)
    precision = len(matches) / len(generated_nodes['marbles'])
    recall = len(matches) / len(generated_nodes['holes'])
    f_score = 2 * precision * recall / (precision + recall)
    return precision, recall, f_score


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluating map inference using hole/marble method to get precision/recall/f-score')
    parser.add_argument('--ground_map_path', type=str, help='Path to ground truth map in shape format (.shp)')
    parser.add_argument('--infer_map_dbpath', type=str, help='Path to inferenc ground truth map in shape format (.shp)')
    args = parser.parse_args()

    ground_truth_path = args.ground_map_path
    ground_map = gp.read_file(ground_truth_path)
    gt_edges = ground_map['geometry'].apply(lambda x: np.array(x.coords)[:, ::-1])
    con = sqlite3.connect("skeleton_maps/skeleton_map_1m.db")
    edges_df = pd.read_sql_query("SELECT id, in_node, out_node, weight FROM edges", con)
    nodes_df = pd.read_sql_query("SELECT id, latitude, longitude, weight FROM nodes", con)
    nodes_df.set_index('id', drop=True, inplace=True)
    # find the start and end nodes coordinates for each edge of the edges table
    # based on nodes of the nodes table
    pr_edges = edges_df.apply(lambda x: np.array([
        [nodes_df.loc[x.in_node].latitude, nodes_df.loc[x.in_node].longitude],
        [nodes_df.loc[x.out_node].latitude, nodes_df.loc[x.out_node].longitude]
    ]), axis=1)
    r, d, check_threshold, error_threshold = 1000, 100, 0.15, 50
    gt_nodes_dict = generate_node_mapping(gt_edges)
    pr_nodes_dict = generate_node_mapping(pr_edges)
    new_gen_nodes = generate_nodes(gt_nodes_dict, pr_nodes_dict, r, d, check_threshold)
    precision, recall, f_score = evalute_prf(new_gen_nodes, error_threshold)
    print(precision, recall, f_score)