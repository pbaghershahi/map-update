from filtering import load_data, trajToShape, load_directory
import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--data_directory', type=str, help='Directory to data folders')
    parser.add_argument('--csv_output_directory', type=str, help='Directory to save csv data')
    parser.add_argument('--shape_output_directory', type=str, help='Directory to save trajectories shape files (.shp)')
    parser.add_argument('--from_directory', type=bool, default=False, help='load and write all data at once.')
    args = parser.parse_args()

    with open(args.bounding_box_path, 'r') as bbx_file:
        north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    boundary = dict(
        east=east,
        west=west,
        north=north,
        south=south
    )
    if args.from_directory:
        boundary = dict(east=51.431343, west=51.407055, north=35.72351, south=35.71129)
        _ = load_directory(
            dir_path=args.data_directory,
            boundary=boundary,
            output_dir=args.csv_output_directory,
            shape_path=args.shape_output_directory,
            has_distance=True
        )
    else:
        _ = load_data(args.data_directory, boundary, args.csv_output_directory)
        traj_directory = '/'.join(args.shape_output_directory.split('/')[:-1])
        if not os.path.exists(traj_directory):
            os.makedirs(traj_directory)
        trajToShape(args.csv_output_directory, args.shape_output_directory)
