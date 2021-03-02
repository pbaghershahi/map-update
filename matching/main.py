
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

from fmm import GPSConfig,ResultConfig, Network,NetworkGraph,STMATCH,STMATCHConfig
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map matching using FMM algorithm')
    parser.add_argument('--n_candidates', type=int, default=8, help='Number of candidates (default:8)')
    parser.add_argument('--gps_error', type=float, default=0.5, help='GPS sensor error (unit: map unit) (default:0.5)')
    parser.add_argument('--radius', type=float, default=0.0002, help='Search radius (unit: map unit) (default:300)')
    parser.add_argument('--vmax', type=float, default=30,
                        help='Maximum vehicle speed (unit: map unit), only applicable for stmatch (default:30)')
    parser.add_argument('--factor', type=float, default=1.5,
                        help='Factor to limit shortest path search, only applicable for stmatch (default:1.5)')
    parser.add_argument('--ground_map_path', type=str, help='Path to ground truth map in shape format (.shp)')
    parser.add_argument('--filtered_map_path', type=str, default='',
                        help='Path to filtered ground truth map in shape format (.shp)')
    parser.add_argument('--trajs_path', type=str, help='Path to gps trajectories in shape format (.shp)')
    parser.add_argument('--output_file_path', type=str, help='Path to gps trajectories in shape format (.shp)')
    parser.add_argument('--id_column_name', type=str, default='id', help='GPS id field/column name (default:id)')
    parser.add_argument('--write_opath', type=bool, default=False,
                        help='Include edge matched to each point of trajectory in output file (list of int)')
    parser.add_argument('--write_length', type=bool, default=False,
                        help='Include length of the matched edge for each point in output file (list of floats)')
    parser.add_argument('--write_ep', type=bool, default=False,
                        help='Include emission probability in HMM for each matched point in output file (list of floats)')
    parser.add_argument('--write_tp', type=bool, default=False,
                        help='Include transition probability in HMM for two consecutive matched points in output file (list of floats)')
    parser.add_argument('--write_ogeom', type=bool, default=False,
                        help='Include original trajectory geometry in output file (string)')
    parser.add_argument('--write_offset', type=bool, default=False,
                        help='Include distance from the matched point to the start of the matched edge in output file (list of floats)')
    parser.add_argument('--write_error', type=bool, default=False,
                        help='Include distance from each point to its matched point in output file (list of floats)')
    args = parser.parse_args()

    config = STMATCHConfig()
    config.k = args.n_candidates
    config.gps_error = args.gps_error
    config.radius = args.radius
    config.vmax = args.vmax
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
    result_config.output_config.write_length = args.write_length
    result_config.output_config.write_ep = args.write_ep
    result_config.output_config.write_tp = args.write_tp
    result_config.output_config.write_ogeom = args.write_ogeom
    result_config.output_config.write_offset = args.write_offset
    result_config.output_config.write_error = args.write_error

    status = model.match_gps_file(input_config, result_config, config)

    print('*'*20)
    print(result_config.to_string())
    print(status)