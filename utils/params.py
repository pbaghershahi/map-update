import argparse

# matching main
parser = argparse.ArgumentParser(description='Map matching using FMM algorithm!')
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
# ground map
parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
parser.add_argument('--remove_percent', type=float, default=0.2,
                    help='Percentage of edges to be removed from ground truth map')
# trajectory generation
parser.add_argument('--data_directory', type=str, help='Directory to data folders')
parser.add_argument('--csv_output_directory', type=str, help='Directory to save csv data')
parser.add_argument('--shape_output_directory', type=str, help='Directory to save trajectories shape files (.shp)')
args = parser.parse_args()
