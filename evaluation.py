import pandas as pd
import geopandas as gp
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
import datetime
from shapely import wkb
import argparse, os
import osmnx as ox
from haversine import haversine, Unit


def cos_similarity(a, b):
    return a@b/(np.linalg.norm(a)*np.linalg.norm(b))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate Algorithm Performance by Precision, Recall, F1-score')
    parser.add_argument('--match_path', type=str,
                        help='Path to unmatched matching of dropped edges and unmatched edges in csv format (.csv)')
    parser.add_argument('--trajs_match', type=str,
                        help='Path to trajectories matching of all edges and trajectory edges in csv format (.csv)')
    parser.add_argument('--inferred_edges_path', type=str,
                        help='Path to inferred edges in shape format (.shp)')
    parser.add_argument('--dropped_map_path', type=str, default='',
                        help='Path to saved dropped ground truth map in shape format (.shp)')
    parser.add_argument('--cut_thresh', type=float, default=25,
                        help='threshold to filter unmatched edges and dropped edges by cosine similarity in degrees')
    parser.add_argument('--min_len', type=float, default=20,
                        help='minimum length of dropped edges which the algorithm can infer in meters')
    parser.add_argument('--min_crossing', type=int, default=1,
                        help='minimum number of crossing from dropped edges which the algorithm can infer')
    parser.add_argument('--results_save_path', type=str, default='results.txt',
                        help='path to save evaluation results in .txt format')
    args = parser.parse_args()

    # matches = pd.read_csv('./data/unmatched_mr.csv', sep=';', index_col='id', engine='python')
    matches = pd.read_csv(args.match_path, sep=';', index_col='id', engine='python')
    # trajs_matches = pd.read_csv('./data/trajs_mr.csv', sep=';', index_col='id', engine='python')
    trajs_matches = pd.read_csv(args.trajs_match, sep=';', index_col='id', engine='python')
    trajs_matches = trajs_matches[trajs_matches.opath.notna()]
    # edges = gp.read_file('./data/inferred-edges/edges.shp')
    edges = gp.read_file(args.inferred_edges_path)
    edges.set_index('id', drop=True, inplace=True)

    unmatches = matches[matches.unmatch == False]
    unmatches['cross_edges'] = None

    # dropped_edges = gp.read_file('./ground-map/map/dropped_edges.shp')
    dropped_edges = gp.read_file(args.dropped_map_path)
    dropped_edges.set_index('id', drop=True, inplace=True)

    for index, row in unmatches.iterrows():
        gen_edge = np.array(edges.loc[index].geometry.coords)
        gen_edge = gen_edge[0] - gen_edge[-1]
        matched_edges = []
        for edge_id in [int(x) for x in row.opath.split(',')]:
            gt_edge = np.array(dropped_edges.loc[edge_id].geometry.coords)
            gt_edge = gt_edge[0] - gt_edge[-1]
            cos_sim = abs(cos_similarity(gen_edge, gt_edge))
            if cos_sim >= np.cos(np.radians(args.cut_thresh)):
                matched_edges.append(str(edge_id))
        if len(matched_edges) > 0:
            unmatches.cross_edges.loc[index] = ','.join(matched_edges)

    dropped_edges = dropped_edges[dropped_edges.way_length > args.min_len]
    dropped_edges['num_trips'] = 0
    for match_idx, row in trajs_matches.iterrows():
        for edge_idx in [int(k) for k in row.opath.split(',')]:
            if edge_idx in dropped_edges.index:
                dropped_edges.num_trips.loc[edge_idx] += 1
    dropped_edges = dropped_edges[dropped_edges.num_trips >= args.min_crossing]

    crossed_edges = set()
    for index, row in unmatches[unmatches.cross_edges.notna()].iterrows():
        crossed_edges = crossed_edges.union(set([int(x) for x in row.cross_edges.split(',')]))

    total_unmatched_edges = matches.shape[0]
    total_dropped_edges = dropped_edges.shape[0]
    num_true_edges = len(crossed_edges)
    precision = num_true_edges/total_unmatched_edges
    recall = num_true_edges/total_dropped_edges
    f1_score = 2 * precision * recall / (precision + recall)
    result_txt = f'{"*"*20}Final results:{"*"*20}\n'\
                 f'Total number of inferred edges: {total_unmatched_edges}\n'\
                 f'Total number of dropped edges: {total_dropped_edges}\n'\
                 f'Number of correctly detected edges: {num_true_edges}\n'\
                 f'Precision: {precision}\n'\
                 f'Recall: {recall}\n'\
                 f'F1-score: {f1_score}'

    output_dir = '/'.join(args.results_save_path.split('/')[:-1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(args.results_save_path, 'w') as result_file:
        result_file.write(result_txt)
    print(result_txt)