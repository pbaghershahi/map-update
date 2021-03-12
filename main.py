import argparse
import numpy as np
import geopandas as gp
from filtering import load_unmatched
import pandas as pd


def compute_score(x):
    if pd.isna(x[0]):
        return x[0]
    ep = [float(y) for y in x[0].split(',')]
    tp = [float(y) for y in x[1].split(',')]
    tp[0] = 1
    score = [ep[i] * tp[i] for i in range(len(ep))]
    # score = ','.join([str(ep[i] * tp[i]) for i in range(len(ep))])
    return sum(score)/len(score)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map matching using FMM algorithm')
    parser.add_argument('--matches_file_path', type=str, help='Path to matches file in csv format')
    parser.add_argument('--output_directory', type=str, help='Path to save output file in csv format')
    parser.add_argument('--data_directory', type=str, help='Directory to data folders')
    parser.add_argument('--add_score', type=bool, default=True,
                        help='Add mean score column to the matches dataframe')
    parser.add_argument('--low_threshold', type=float, default=0.3,
                        help='Low threshold to filter data for include unmatched trajectories')
    parser.add_argument('--high_threshold', type=float, default=0.5,
                        help='High threshold to filter data for include unmatched trajectories')
    args = parser.parse_args()

    # matches = pd.read_csv(args.matches_file_path, sep=';', index_col='id', engine='python')
    # unmatched_indices = matches[matches.unmatch == True].index
    # _ = load_unmatched(args.data_directory, unmatched_indices, args.output_directory)
    if args.add_score:
        matches = pd.read_csv(args.matches_file_path, sep=';', index_col='id', engine='python')
        matches['score'] = matches[['ep', 'tp']].apply(compute_score, axis=1)
        low_threshold = np.exp(-0.5*(args.low_threshold/args.gps_error))
        high_threshold = np.exp(-0.5*(args.high_threshold/args.gps_error))
        # matches['unmatch'] = matches['error'].apply(
        #     lambda e: any([60/METERS_PER_DEGREE_LATITUDE < float(x) < args.cutoff/METERS_PER_DEGREE_LATITUDE for x in e.split(',')]) if pd.notna(e) else False
        # )
        print(f'Threshold between: [{high_threshold}, {low_threshold}]')
        matches['unmatch'] = matches['ep'].apply(
            lambda e: any([high_threshold < float(x) < low_threshold for x in e.split(',')]) if pd.notna(e) else False
        )

        # matches['unmatch'] = matches['score'].apply(
        #     lambda e: high_threshold < float(e) < low_threshold if pd.notna(e) else False
        # )
        matches.to_csv(args.matches_file_path, sep=';', header=True, index=True)


