import pandas as pd
import os, csv

# unmatch_set = [
#     26628, 28678, 22536, 12305, 34845, 32802, 34853, 34871, 2115, 26707, 34908, 18528, 24689, 34945, 26756, 30853,
#     12432, 32915, 30881, 32929, 24751, 26800, 20658, 32952, 35018, 28876, 35022, 26833, 26835, 6365, 35043, 33002,
#     16625, 35057, 33014, 22777, 35070, 26882, 30979, 28934, 18696, 35083, 33040, 35103, 8483, 28968, 28978, 10551,
#     26938, 20798, 26943, 31047, 35148, 35151, 35152, 26962, 33110, 14692, 29031, 16748, 35191, 22907, 35206, 18825,
#     29066, 35210, 33174, 24986, 35229, 14753, 22952, 29097, 35241, 33216, 35266, 31173, 33223, 35280, 35281, 35282,
#     31189, 29143, 14812, 29149, 33244, 33273, 27135, 27140, 16904, 35357, 33310, 35359, 29220, 29222, 33327, 35397,
#     33352, 35405, 23120, 33361, 33366, 31330, 33378, 29287, 33390, 31358, 10886, 29331, 31391, 35489, 33449, 31406,
#     31409, 33458, 35507, 12985, 25290, 25291, 35537, 33502, 17131, 27372, 25341, 33536, 19208, 17166, 33554, 25376,
#     35616, 19238, 35622, 35627, 820, 4918, 823, 35641, 35657, 35658, 21344, 35685, 35686, 29553, 888, 31619, 21386,
#     35739, 35740, 33693, 35747, 23467, 29624, 31672, 35773, 25553, 31709, 35805, 33779, 25600, 31749, 31750, 25611,
#     21516, 27664, 33812, 7190, 35864, 29722, 7196, 33831, 11312, 27704, 35897, 9274, 27711, 27715, 27716, 9292, 21583,
#     5200, 35929, 17506, 31846, 25712, 19593, 23695, 35984, 35986, 36016, 29876, 36023, 29886, 36040, 25811, 36052,
#     34005, 25819, 31964, 36069, 36070, 36074, 29935, 13552, 27904, 29958, 29959, 32006, 34057, 36104, 36108, 36111,
#     32016, 34065, 29971, 36117, 36128, 30003, 19767, 32060, 34108, 27975, 30024, 27979, 27992, 34136, 34148, 34152,
#     32107, 19824, 32117, 34184, 34190, 21917, 34206, 28063, 36256, 32163, 17839, 34225, 30131, 34227, 36295, 1491,
#     36316, 19935, 21989, 11755, 26093, 28149, 36348, 36351, 36352, 32260, 30221, 36375, 34335, 28195, 30246, 28199,
#     30247, 26159, 28207, 32304, 5682, 34357, 36407, 34362, 9798, 9799, 26182, 1641, 30321, 32374, 36471, 36482, 13956,
#     34437, 34441, 22160, 7828, 22178, 9898, 34481, 34490, 36542, 34495, 11989, 36573, 20190, 32480, 32481, 32499, 14078,
#     32518, 34575, 36624, 36625, 26403, 32559, 32581, 30539, 32598, 34671, 30581, 32643, 34717, 18344, 20408, 32705,
#     34760, 18379, 18381, 14288, 20439, 34789, 30694, 30695, 20456, 34809
# ]
#
# def load_data(file_path, unmatches, file_dist):
#     if os.path.exists(file_path) is not True:
#         print('Path does not exists!')
#         return
#     unmatch_trajs = []
#     for dir_name in [x for x in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, x)) and not x.startswith('.')]:
#         if not os.path.exists(file_dist + '/unmatch'):
#             os.makedirs(file_dist + '/unmatch')
#         files = sorted(os.listdir(os.path.join(file_path, dir_name)))
#         for file in files:
#             if not file.endswith('.csv'):
#                 continue
#             full_path = os.path.join(file_path, dir_name, file)
#             print(full_path)
#             temp_csv = pd.read_csv(full_path, sep=',', engine='python')
#             for index, row in temp_csv.iterrows():
#                 if int(row.route_id) in unmatches:
#                     unmatch_trajs.append(list(row.values))
#
#     file_name = file_dist + '/unmatch/unmatch.csv'
#     with open(file_name, 'w') as csv_file:
#         csv_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
#         csv_writer.writerow(['route_id', 'longitude', 'latitude', 'timestamp', 'bearing', 'speed'])
#         for trajectory in unmatch_trajs:
#             csv_writer.writerow(trajectory)
#     return file_dist
#
# load_data('./data/gps-csv/', unmatch_set,'./data/')
from filtering import edgeToShape

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--map_dbpath', type=str, help='Path to map sqlite database file')
    parser.add_argument('--shape_output_path', type=str, help='Directory to save inferred edges shape files (.shp)')
    parser.add_argument('--n_edge_splits', type=int, default=5, help='Number of edge splits')
    args = parser.parse_args()

    edgeToShape(args.map_dbpath, args.shape_output_path, args.n_edge_splits)


