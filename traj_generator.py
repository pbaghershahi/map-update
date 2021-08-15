from filtering import load_data, trajToShape, load_directory, datsetToUTM
import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--data_directory', type=str, help='Directory to data folders')
    parser.add_argument('--csv_output_directory', type=str, help='Directory to save csv data')
    parser.add_argument('--shape_output_directory', type=str, help='Directory to save trajectories shape files (.shp)')
    parser.add_argument('--from_directory', type=bool, default=False, help='load and write all data at once.')
    parser.add_argument('--large_size_files', type=bool, default=False,
                        help='if parquet files are large size. (default: False)')
    parser.add_argument('--has_distance', type=bool, default=False,
                        help='if parquet files has column. (default: False)')
    parser.add_argument('-utm', '--convert-to-utm', action='store_true', default=False)
    parser.add_argument('--utm-out-dir', type=str, help='path to save output csv files in utm coordinates')
    args = parser.parse_args()

    with open(args.bounding_box_path, 'r') as bbx_file:
        north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    boundary = dict(
        east=east,
        west=west,
        north=north,
        south=south
    )
    if args.large_size_files:
        large_size_files = True
    else:
        large_size_files = False
    if args.has_distance:
        has_distance = True
    else:
        has_distance = False
    if args.from_directory:
        _ = load_directory(
            dir_path=args.data_directory,
            boundary=boundary,
            output_dir=args.csv_output_directory,
            shape_path=args.shape_output_directory,
            has_distance=has_distance,
            large_size=large_size_files,
            start_time='2021-06-06 00:00:00',
            end_time='2021-06-06 23:59:59'
        )
    else:
        csvfiles_dir = load_data(args.data_directory, boundary, args.csv_output_directory)
        traj_directory = '/'.join(args.shape_output_directory.split('/')[:-1])
        if not os.path.exists(traj_directory):
            os.makedirs(traj_directory)
        trajToShape(csvfiles_dir, args.shape_output_directory)
        # trajToShape('./data/gps-csv/sample-area/', args.shape_output_directory)

    if args.convert_to_utm:
        datsetToUTM(args.csv_output_directory, args.utm_out_dir)