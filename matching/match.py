
########################################## PLEASE READ THE FOLLOWING ####################################

"""
We make use of fmm package which is an HMM-based method for map matching.

This package is not available on PyPI but you clone it from this link: https://github.com/cyang-kth/fmm

After cloning read the instructions for installation from this link: https://fmm-wiki.github.io/docs/installation/
for example to install on ubuntu os you should follow the steps bellow:
1- sudo add-apt-repository ppa:ubuntugis/ppa
2- sudo apt-get -q update
3- sudo apt-get install libboost-dev libboost-serialization-dev gdal-bin libgdal-dev make cmake libbz2-dev libexpat1-dev swig python-dev
4- mkdir build (Under the project folder which you have cloned)
5- cd build
6- cmake ..
7- make -j4
8- sudo make install
"""

from fmm import GPSConfig, ResultConfig, Network, NetworkGraph, STMATCH, STMATCHConfig
import argparse
import pandas as pd
import geopandas as gp
import numpy as np

METERS_PER_DEGREE_LATITUDE = 111120
METERS_PER_DEGREE_LONGITUDE = 90329


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
    parser.add_argument('--n_candidates', type=int, default=4, help='Number of candidates (default:8)')
    parser.add_argument('--gps_error', type=float, default=40, help='GPS sensor error (unit: map unit) (default:50)')
    # parser.add_argument('--radius', type=float, default=0.0002, help='Search radius (unit: map unit) (default:300)')
    parser.add_argument('--radius', type=float, default=300, help='Search radius (unit: map unit) (default:300)')
    parser.add_argument('--vmax', type=float, default=30,
                        help='Maximum vehicle speed (unit: map unit), only applicable for stmatch (default:30)')
    parser.add_argument('--factor', type=float, default=1.5,
                        help='Factor to limit shortest path search, only applicable for stmatch (default:1.5)')
    parser.add_argument('--ground_map_path', type=str, help='Path to ground truth map in shape format (.shp)')
    parser.add_argument('--filtered_map_path', type=str, default='',
                        help='Path to filtered ground truth map in shape format (.shp)')
    parser.add_argument('--trajs_path', type=str, help='Path to gps trajectories in shape format (.shp)')
    parser.add_argument('--output_file_path', type=str, help='Path to save output file in csv format')
    parser.add_argument('--id_column_name', type=str, default='id', help='GPS id field/column name (default:id)')
    parser.add_argument('--write_opath', type=bool, default=False,
                        help='Include edge matched to each point of trajectory in output file (list of int)')
    parser.add_argument('--write_cpath', type=bool, default=True,
                        help='Include the path traversed by the trajectory in output file (list of int)')
    parser.add_argument('--write_length', type=bool, default=False,
                        help='Include length of the matched edge for each point in output file (list of floats)')
    parser.add_argument('--write_ep', type=bool, default=True,
                        help='Include emission probability in HMM for each matched point in output file (list of floats)')
    parser.add_argument('--write_tp', type=bool, default=True,
                        help='Include transition probability in HMM for two consecutive matched points in output file (list of floats)')
    parser.add_argument('--write_ogeom', type=bool, default=False,
                        help='Include original trajectory geometry in output file (string)')
    parser.add_argument('--write_mgeom', type=bool, default=False,
                        help='Include the geometry of the cpath in output file (string)')
    parser.add_argument('--write_offset', type=bool, default=False,
                        help='Include distance from the matched point to the start of the matched edge in output file (list of floats)')
    parser.add_argument('--write_error', type=bool, default=True,
                        help='Include distance from each point to its matched point in output file (list of floats)')
    parser.add_argument('--add_score', type=bool, default=False,
                        help='Add mean score column to the matches dataframe')
    parser.add_argument('--low_threshold', type=float, default=0.3,
                        help='Low threshold to filter data for include unmatched trajectories')
    parser.add_argument('--high_threshold', type=float, default=0.5,
                        help='High threshold to filter data for include unmatched trajectories')
    parser.add_argument('--n_edge_split', type=int, default=9,
                        help='Number of edge splits (default:9)')
    parser.add_argument('--overlap_portion', type=float, default=0.5,
                        help='Portion of the trajectory which should overlap with existing edge')
    parser.add_argument('--save_unmatched', type=bool, default=False,
                        help='Flag to save unmatched results or not only available if add_score is True')
    args = parser.parse_args()

    config = STMATCHConfig()
    config.k = args.n_candidates

    config.gps_error = args.gps_error/METERS_PER_DEGREE_LATITUDE
    config.radius = args.radius/METERS_PER_DEGREE_LATITUDE
    config.vmax = args.vmax/METERS_PER_DEGREE_LATITUDE

    config.factor = args.factor

    network = Network(args.ground_map_path)
    graph = NetworkGraph(network)
    print(graph.get_num_vertices())
    model = STMATCH(network, graph)

    input_config = GPSConfig()
    input_config.file = args.trajs_path
    input_config.id = args.id_column_name

    print(input_config.to_string())
    print('*'*20)

    result_config = ResultConfig()
    result_config.file = args.output_file_path
    result_config.output_config.write_opath = args.write_opath
    result_config.output_config.write_cpath = args.write_cpath
    result_config.output_config.write_length = args.write_length
    result_config.output_config.write_ep = args.write_ep
    result_config.output_config.write_tp = args.write_tp
    result_config.output_config.write_ogeom = args.write_ogeom
    result_config.output_config.write_mgeom = args.write_mgeom
    result_config.output_config.write_offset = args.write_offset
    result_config.output_config.write_error = args.write_error

    status = model.match_gps_file(input_config, result_config, config)

    if args.add_score:
        matches = pd.read_csv(args.output_file_path, sep=';', engine='python')
        edges = gp.read_file(args.trajs_path)
        edges.set_index('id', drop=True, inplace=True)
        # matches['score'] = matches[['ep', 'tp']].apply(compute_score, axis=1)
        # low_threshold = np.exp(-0.5*(args.low_threshold/args.gps_error))
        # high_threshold = np.exp(-0.5*(args.high_threshold/args.gps_error))

        low_threshold = 0
        high_threshold = args.n_edge_split*args.overlap_portion

        print(f'Threshold between: [{high_threshold}, {low_threshold}]')

        matches['sum_score'] = matches['ep'].apply(
            lambda e: sum([float(x) for x in e.split(',')]) if pd.notna(e) else np.nan
        )
        matches['unmatch'] = matches['sum_score'].apply(
            lambda e: low_threshold < float(e) < high_threshold if pd.notna(e) else False
        )

        # matches['unmatch'] = matches['opath'].apply(
        #     lambda e: len(set(e.split(','))) != 1 if pd.notna(e) else False
        # )

        nan_indices = sorted(list((set(edges.index)-set(matches.id))))
        matches['id'][matches.error.isna()] = nan_indices
        matches.set_index('id', drop=True, inplace=True)
        matches.loc[nan_indices, 'unmatch'] = True

        matches.to_csv(args.output_file_path, sep=';', header=True, index=True)

        if args.save_unmatched:
            unmatched_indices = matches[matches.unmatch == True].index
            unmatched_edges = edges[edges.index.isin(unmatched_indices)]
            unmatched_edges = gp.GeoDataFrame(unmatched_edges, geometry='geometry')
            unmatched_edges.to_file('./data/unmatched.shp', driver='ESRI Shapefile')



    print('*'*20)
    print(result_config.to_string())
    print(status)