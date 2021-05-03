import matplotlib.pyplot as plt
import osmnx as ox
import geopandas as gp, pandas as pd
from haversine import haversine, Unit
import numpy as np
import subprocess
import argparse, os


def filter_bound(x, bound):
    coords = x.coords
    in_bound = (bound['west'] < coords[0][0] < bound['east']) and \
    (bound['west'] < coords[-1][0] < bound['east']) and \
    (bound['south'] < coords[0][1] < bound['north']) and \
    (bound['south'] < coords[-1][1] < bound['north'])
    return in_bound

def execute(cmd):
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    (result, error) = process.communicate()
    rc = process.wait()
    if rc != 0:
        print("Error: failed to execute command: ", cmd)
        print(error.rstrip().decode("utf-8"))
    return result.rstrip().decode("utf-8"), error.rstrip().decode("utf-8")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load map graph from openstreetmap')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--drop_seed', type=int, default=2021, help='Initial seed to remove edges from map randomly')
    parser.add_argument('--remove_percent', type=float, default=0.1,
                        help='Percentage of edges to be removed from ground truth map')
    parser.add_argument('--min_edge_length', type=float, default=20,
                        help='Minimum distance of edges which can be detected (in meters)')
    parser.add_argument('--ground_map_path', type=str, help='Path to save ground truth map in shape format (.shp)')
    parser.add_argument('--output_file_path', type=str, default='', help='Path to save matching result in csv format')
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
    parser.add_argument('--global_map', type=bool, default=False,
                        help='process for global map (default: False)')
    parser.add_argument('--trajs_path', type=str, default='',
                        help='Path to trajectories in .shp format')
    parser.add_argument('--min_len', type=float, default=20,
                        help='minimum length of dropped edges which the algorithm can infer in meters')
    parser.add_argument('--min_crossing', type=int, default=1,
                        help='minimum number of crossing from dropped edges which the algorithm can infer')
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
    # edges.columns = ['osmid', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'way_length', 'lanes', 'junction', 'bridge', 'landuse', 'tunnel', 'geometry', 'source', 'target', 'key']
    edges = edges[['oneway', 'highway', 'length', 'geometry', 'u', 'v']]
    edges.columns = ['oneway', 'highway', 'way_length', 'geometry', 'source', 'target']
    # print('here in ground ********************************')
    # edges = edges[edges.way_length > args.min_edge_length]
    np.random.seed(args.drop_seed)
    r_percent = args.remove_percent
    edges['id'] = range(len(edges))
    edges = edges[['id', 'source', 'target', 'geometry', 'way_length', 'highway']]
    edges['id'] = edges['id'].apply(lambda x: x[0] if type(x) == list else x)
    # print(edges)
    if args.global_map:
        output_dir = '/'.join(args.ground_map_path.split('/')[:-1])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        edges.to_file(args.ground_map_path)
        results, errors = execute(f'python matching/match.py --ground_map_path {args.ground_map_path} --trajs_path {args.trajs_path} --output_file_path {args.output_file_path} --write_opath True --radius 100 --gps_error 40')
        # print('herrrrrrreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee: ')
        # print(results)
        # print('thhheeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeerrrrrrrrrrrrrrrrrr')
        # print(errors)
        # print('hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiilllllllllllllllllllllleeeeee')
        print(results)
        print(errors)
        trajs_matches = pd.read_csv(args.output_file_path, sep=';', index_col='id', engine='python')
        trajs_matches = trajs_matches[trajs_matches.opath.notna()]
        all_edges = edges.set_index('id', drop=True)
        all_edges['long'] = all_edges.way_length.apply(lambda x: x > args.min_len)
        all_edges['num_trips'] = 0
        for match_idx, row in trajs_matches.iterrows():
            for edge_idx in [int(k) for k in row.opath.split(',')]:
                if edge_idx in all_edges.index:
                    # print('before', all_edges.loc[edge_idx, 'num_trips'])
                    all_edges.loc[edge_idx, 'num_trips'] += 1
                    # print('after', all_edges.loc[edge_idx, 'num_trips'])
        all_edges['common'] = all_edges.num_trips.apply(lambda x: x >= args.min_crossing)
        all_edges.to_file(args.ground_map_path, index=True)
    else:
        all_edges = gp.read_file(args.ground_map_path)
        # print(edges)
        # print(all_edges)
        all_edges.set_index('id', drop=True, inplace=True)
        merged = pd.merge(edges, all_edges, on=['source', 'target'], left_index=True, indicator=True)
        # print(merged)
        merged = merged[merged['_merge']=='both']
        all_edges = all_edges.loc[merged.index]
        bound = {'east': east, 'west': west, 'south': south, 'north': north}
        all_edges['in_bound'] = all_edges.geometry.apply(
            lambda x: filter_bound(x, bound)
        )
        # print(all_edges[
        #         (all_edges.highway == 'residential') &
        #         (all_edges.in_bound == True) &
        #         (all_edges.long == True) &
        #         (all_edges.common == True)
        #         ])
        # all_edges[all_edges.highway.isin(['secondary', 'residential'])].plot()
        # plt.show()
        # print(len(all_edges))
        # print(all_edges.highway.unique())
        candidates = all_edges[
            all_edges.highway.isin(['secondary', 'residential']) &
            (all_edges.in_bound == True) &
            (all_edges.long == True) &
            (all_edges.common == True)
        ].index
        # print(candidates)
        drop_indices = np.random.choice(
            candidates, max(min(15, len(candidates)), int(r_percent * len(candidates))), replace=False
        )
        # print(drop_indices)
        output_dir = '/'.join(args.filtered_map_path.split('/')[:-1])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        dropped_edges = all_edges.loc[drop_indices]
        filtered_edges = all_edges.drop(drop_indices)
        filtered_edges.to_file(args.filtered_map_path)
        dropped_edges.to_file(args.dropped_map_path)
