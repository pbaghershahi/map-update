import osmnx as ox
import geopandas as gp

import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load map graph from openstreetmap')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--remove_percent', type=float, default=0.2,
                        help='Percentage of edges to be removed from ground truth map')
    parser.add_argument('--ground_map_path', type=str, help='Path to save ground truth map in shape format (.shp)')
    parser.add_argument('--filtered_map_path', type=str, default='',
                        help='Path to save filtered ground truth map in shape format (.shp)')
    args = parser.parse_args()

    with open(args.bounding_box_path, 'r') as bbx_file:
        north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    graph = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False, retain_all=True)
    nodes, edges = ox.graph_to_gdfs(graph)
    print(edges.columns)

    # edges.columns = ['osmid', 'oneway', 'highway', 'length', 'ref', 'name', 'maxspeed', 'lanes', 'bridge', 'junction', 'geometry', 'source', 'target', 'key']
    edges.columns = ['osmid', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'length', 'lanes', 'junction', 'bridge', 'landuse', 'tunnel', 'geometry', 'source', 'target', 'key']
    r_percent = args.remove_percent
    drop_indices = np.random.choice(edges[(edges.highway == 'residential')].index, int(r_percent*len(edges)), replace=False)
    edges['id'] = range(len(edges))
    all_edges = edges[['id', 'source', 'target', 'geometry']]
    all_edges['id'] = all_edges['id'].apply(lambda x: x[0] if type(x) == list else x)
    filtered_edges = all_edges.drop(drop_indices)
    all_edges.to_file(args.ground_map_path)
    # df = gp.read_file('./map/all_edges.shp')
    # print(df)
    filtered_edges.to_file(args.filtered_map_path)
    # df = gp.read_file('./map/filtered_edges.shp')
    # print(df)