import geopandas as gp
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import pandas as pd
from haversine import haversine, Unit
import osmnx as ox
import argparse, os
import numpy as np
from matplotlib.colors import ListedColormap


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
    parser.add_argument('--filtered_map_path', type=str, default='',
                        help='Path to saved filtered ground truth map in shape format (.shp)')
    parser.add_argument('--all_map_path', type=str, default='',
                        help='Path to saved all ground truth map in shape format (.shp)')
    parser.add_argument('--cut_thresh', type=float, default=25,
                        help='threshold to filter unmatched edges and dropped edges by cosine similarity in degrees')
    parser.add_argument('--min_len', type=float, default=20,
                        help='minimum length of dropped edges which the algorithm can infer in meters')
    parser.add_argument('--min_crossing', type=int, default=5,
                        help='minimum number of crossing from dropped edges which the algorithm can infer')
    parser.add_argument('--plot_matches', type=bool, default=False,
                        help='plot matched results (default: False)')
    parser.add_argument('--plot_all_edges', type=bool, default=False,
                        help='plot all inferred edges (default: False)')
    parser.add_argument('--background_map', type=str, default='dropped',
                        help='map on the background options: "dropped" and "filtered" (default: dropped)')
    parser.add_argument('--figure_save_path', type=str, default='result.png', help='path to save figure in .png format')
    parser.add_argument('--apply_cos_sim', type=bool, default=False,
                        help='filter true true edges based on cosine similarity (default: False)')
    parser.add_argument('--false_edges', type=bool, default=False,
                        help='Just draw False edges (default: False)')

    args = parser.parse_args()

    matches = pd.read_csv(args.match_path, sep=';', index_col='id', engine='python')
    trajs_matches = pd.read_csv(args.trajs_match, sep=';', index_col='id', engine='python')
    trajs_matches = trajs_matches[trajs_matches.opath.notna()]
    edges = gp.read_file(args.inferred_edges_path)
    edges.set_index('id', drop=True, inplace=True)

    if not args.plot_matches:
        plot_matches = False
    else:
        plot_matches = True
    unmatches = matches[matches.unmatch==plot_matches]

    dropped_edges = gp.read_file(args.dropped_map_path)
    dropped_edges.set_index('id', drop=True, inplace=True)

    if (not args.apply_cos_sim) or plot_matches:
        unmatched_indices = unmatches.index
    else:
        unmatches['cross_edges'] = None
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
        unmatched_indices = unmatches[unmatches.cross_edges.notna()].index
        if args.false_edges:
            unmatched_indices = list(
                (set(unmatches.index)-set(unmatched_indices)).union(matches[matches.unmatch==True].index)
            )

    if not args.plot_all_edges:
        unmatched_edges = edges[edges.index.isin(unmatched_indices)]
    else:
        unmatched_edges = edges

    fig, ax = plt.subplots(figsize=(12, 8))
    cmap = ListedColormap(['yellow'])

    if args.background_map == 'dropped':
        len_ommited = dropped_edges[dropped_edges.way_length < args.min_len]
        dropped_edges = dropped_edges[dropped_edges.way_length >= args.min_len]
        dropped_edges['num_trips'] = 0
        for match_idx, row in trajs_matches.iterrows():
            for edge_idx in [int(k) for k in row.opath.split(',')]:
                if edge_idx in dropped_edges.index:
                    dropped_edges.num_trips.loc[edge_idx] += 1
        cross_ommited = dropped_edges[dropped_edges.num_trips < args.min_crossing]
        ommited = pd.concat([len_ommited, cross_ommited], ignore_index=True)
        dropped_edges = dropped_edges[dropped_edges.num_trips >= args.min_crossing]
        cross_ommited.plot(color='y', ax=ax, legend=True, alpha=0.3, label='not enough crossings')
        dropped_edges.plot(color='b', ax=ax, legend=True, label='dropped edges')
    elif args.background_map == 'filtered':
        filtered_edges = gp.read_file(args.filtered_map_path)
        filtered_edges.set_index('id', drop=True, inplace=True)
        filtered_edges.plot(color='b', ax=ax, legend=True, label='filtered edges')
    else:
        print('Not a valid background!')


    counter = 0
    for index, row in unmatched_edges.iterrows():
        coords = list(row.geometry.coords)
        if counter == len(unmatched_edges)-1:
            plotting = ax.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r', label='detected edges')
        else:
            plotting = ax.plot([coords[0][0], coords[-1][0]], [coords[0][1], coords[-1][1]], c='r')
        counter += 1

    output_dir = '/'.join(args.figure_save_path.split('/')[:-1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ax.legend()
    fig.savefig(args.figure_save_path, dpi=300)
    # plt.show()