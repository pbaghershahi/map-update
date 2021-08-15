import pandas as pd
from datetime import datetime
from tqdm import tqdm
import os
from filtering import convert_location


def get_loc_boundary(dir_path, out_bound_file):
    min_lat, min_lon, max_lat, max_lon = 1e3, 1e3, 0, 0
    corrupted_files = []
    total_records = 0
    file_paths = sorted([os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)])
    for file_path in tqdm(file_paths, total=len(file_paths)):
        try:
            trajs = pd.read_parquet(file_path)
            total_records += trajs.shape[0]
            trajs.location = trajs.location.apply(
                lambda x: convert_location(x)
            )
            trajs['longitude'] = trajs.location.apply(
                lambda x: x[0]
            )
            trajs['latitude'] = trajs.location.apply(
                lambda x: x[1]
            )
            temp_min_lat, temp_max_lat = trajs.latitude.min(), trajs.latitude.max()
            temp_min_lon, temp_max_lon = trajs.longitude.min(), trajs.longitude.max()
            if temp_min_lat < min_lat:
                min_lat = temp_min_lat
            if temp_max_lat > max_lat:
                max_lat = temp_max_lat
            if temp_min_lon < min_lon:
                min_lon = temp_min_lon
            if temp_max_lon > max_lon:
                max_lon = temp_max_lon
        except:
            corrupted_files.append(file_path)

    print('Corrupted file: ', corrupted_files)
    print('Total number of records: ', total_records)
    print('Total number of files: ', len(file_paths))
    print('Total number of corrupted files: ', len(corrupted_files))
    print(f'Area Boundary: minimum latitude = {min_lat}, '
          f'maximum latitude = {max_lat}, '
          f'minimum longitude = {min_lon}, '
          f'maximum longitude = {max_lon}')
    with open(out_bound_file, 'w') as bbox_file:
        txt2write = f'NORTH_LATITUDE={max_lat}\n' + \
                    f'SOUTH_LATITUDE={min_lat}\n' + \
                    f'EAST_LONGITUDE={max_lon}\n' + \
                    f'WEST_LONGITUDE={min_lon}'
        bbox_file.write(txt2write)


def get_time_boundary(dir_path, out_bound_file):
    min_time, max_time = datetime.max, datetime.min
    file_paths = sorted([os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)])
    for file_path in tqdm(file_paths, total=len(file_paths)):
        try:
            trajs = pd.read_parquet(file_path)
            trajs['timestamp'] = trajs.timestamp.apply(
                lambda x: datetime.fromtimestamp(int(x) / 1000)
            )
            temp_min_time, temp_max_time = trajs.timestamp.min(), trajs.timestamp.max()
            if temp_min_time < min_time:
                min_time = temp_min_time
            if temp_max_time > max_time:
                max_time = temp_max_time
        except:
            pass

    print(f'Time Boundary: minimum timestamp = {min_time}, maximum timestamp = {max_time}')
    with open(out_bound_file, 'w') as bbox_file:
        txt2write = f'MIN_TIMESTAMP={min_time}\n' + \
                    f'MAX_TIMESTAMP={max_time}'
        bbox_file.write(txt2write)

def test(dir_path, out_time_bound_file, out_loc_bound_file):
    north, south, east, west = 35.7384, 35.7185, 51.3822, 51.3200
    start = datetime.fromisoformat('2021-06-06 00:00:00')
    end = datetime.fromisoformat('2021-06-06 23:59:59')
    file_paths = sorted([os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)])
    total_records = 0
    counter = -1
    for file_path in tqdm(file_paths, total=len(file_paths)):
        try:
            counter += 1
            trajs = pd.read_parquet(file_path)
        except:
            os.remove(file_path)
            continue
        trajs['timestamp'] = trajs.timestamp.apply(
            lambda x: datetime.fromtimestamp(int(x) / 1000)
        )
        trajs = trajs[trajs.timestamp.between(start, end)]
        trajs['location'] = trajs.location.apply(
            lambda x: convert_location(x)
        )
        trajs['longitude'] = trajs.location.apply(
            lambda x: x[0]
        )
        trajs['latitude'] = trajs.location.apply(
            lambda x: x[1]
        )
        trajs = trajs[
            trajs.latitude.between(south, north) & trajs.longitude.between(west, east)
        ]
        if trajs.shape[0] > 0:
            print(counter, trajs.shape[0], file_path)
        total_records += trajs.shape[0]

    print(f'Total number of records: {total_records}')

# dir_path = '/home/peymanbi/Downloads/loc-sample/'
dir_path = '/media/peymanbi/Elements/teh_uni_loc_sample_2weeks_entire_city'
out_loc_bound_file = './utils/full_area_loc_bounding_box.txt'
# get_loc_boundary(dir_path, out_loc_bound_file)
out_time_bound_file = './utils/full_area_time_bounding_box.txt'
test(dir_path, out_time_bound_file, out_loc_bound_file)