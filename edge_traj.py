from filtering import edgeToShape
import os

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--map_dbpath', type=str, help='Path to map sqlite database file')
    parser.add_argument('--shape_output_path', type=str, help='Directory to save inferred edges shape files (.shp)')
    parser.add_argument('--n_edge_splits', type=int, default=5, help='Number of edge splits')
    args = parser.parse_args()

    edges_directory = '/'.join(args.shape_output_path.split('/')[:-1])
    if not os.path.exists(edges_directory):
        os.makedirs(edges_directory)
    edgeToShape(args.map_dbpath, args.shape_output_path, args.n_edge_splits)