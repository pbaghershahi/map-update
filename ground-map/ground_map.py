import osmnx as ox
import geopandas as gp
from haversine import haversine, Unit
import numpy as np
import argparse


def filter_bound(x, bound):
    coords = x.coords
    in_bound = (bound['west'] < coords[0][0] < bound['east']) and \
    (bound['west'] < coords[-1][0] < bound['east']) and \
    (bound['south'] < coords[0][1] < bound['north']) and \
    (bound['south'] < coords[-1][1] < bound['north'])
    return in_bound


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load map graph from openstreetmap')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--drop_seed', type=int, default=2021, help='Initial seed to remove edges from map randomly')
    parser.add_argument('--remove_percent', type=float, default=0.1,
                        help='Percentage of edges to be removed from ground truth map')
    parser.add_argument('--min_edge_length', type=float, default=20,
                        help='Minimum distance of edges which can be detected (in meters)')
    parser.add_argument('--ground_map_path', type=str, help='Path to save ground truth map in shape format (.shp)')
    parser.add_argument('--filtered_map_path', type=str, default='',
                        help='Path to save filtered ground truth map in shape format (.shp)')
    parser.add_argument('--dropped_map_path', type=str, default='',
                        help='Path to save dropped ground truth map in shape format (.shp)')
    parser.add_argument('--north_shift', type=float, default=0.0015,
                        help='north expansion value (in latitude unit)')
    parser.add_argument('--south_shift', type=float, default=0.0015,
                        help='south expansion value (in latitude unit)')
    parser.add_argument('--east_shift', type=float, default=0.0015,
                        help='east expansion value (in longitude unit)')
    parser.add_argument('--west_shift', type=float, default=0.0015,
                        help='west expansion value (in longitude unit)')
    args = parser.parse_args()

    with open(args.bounding_box_path, 'r') as bbx_file:
        north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    ox.config(all_oneway=True)
    graph = ox.graph_from_bbox(
        north+args.north_shift,
        south-args.south_shift,
        east+args.east_shift,
        west-args.west_shift,
        network_type='drive', simplify=False, retain_all=True
    )
    nodes, edges = ox.graph_to_gdfs(graph)
    print(edges.columns)

    # edges.columns = ['osmid', 'oneway', 'highway', 'length', 'ref', 'name', 'maxspeed', 'lanes', 'bridge', 'junction', 'geometry', 'source', 'target', 'key']
    edges.columns = ['osmid', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'way_length', 'lanes', 'junction', 'bridge', 'landuse', 'tunnel', 'geometry', 'source', 'target', 'key']
    # edges = edges[edges.way_length > args.min_edge_length]
    np.random.seed(args.drop_seed)
    r_percent = args.remove_percent
    edges['id'] = range(len(edges))
    bound = {'east': east, 'west': west, 'south': south, 'north': north}
    edges['in_bound'] = edges.geometry.apply(
        lambda x: filter_bound(x, bound)
    )
    drop_indices = np.random.choice(
        edges[
            (edges.highway == 'residential') &
            (edges.in_bound == True)
            ].index, int(r_percent * len(edges)), replace=False
    )
    all_edges = edges[['id', 'source', 'target', 'geometry', 'way_length']]
    all_edges['id'] = all_edges['id'].apply(lambda x: x[0] if type(x) == list else x)
    dropped_edges = all_edges.loc[drop_indices]
    filtered_edges = all_edges.drop(drop_indices)
    all_edges.to_file(args.ground_map_path)
    filtered_edges.to_file(args.filtered_map_path)
    dropped_edges.to_file(args.dropped_map_path)
