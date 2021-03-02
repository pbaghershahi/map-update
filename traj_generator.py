from filtering import load_data, trajToShape
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--data_directory', type=str, help='Directory to data folders')
    parser.add_argument('--csv_output_directory', type=str, help='Directory to save csv data')
    parser.add_argument('--shape_output_directory', type=str, help='Directory to save trajectories shape files (.shp)')
    args = parser.parse_args()

    with open(args.bounding_box_path, 'r') as bbx_file:
        north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    files_path = args.data_directory
    boundary = dict(
        east=east,
        west=west,
        north=north,
        south=south
    )
    _ = load_data(files_path, boundary, args.csv_output_directory)
    trajToShape(args.csv_output_directory, args.shape_output_directory)
