from evaluation_utils import traj_partition
import pandas as pd
import geopandas as gp
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
import datetime
from shapely import wkb
import osmnx as ox
from haversine import haversine, Unit
import glob
import os
import subprocess


def execute(cmd):
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    (result, error) = process.communicate()
    rc = process.wait()
    if rc != 0:
        print("Error: failed to execute command: ", cmd)
        print(error.rstrip().decode("utf-8"))
    return result.rstrip().decode("utf-8"), error.rstrip().decode("utf-8")


def partition_area(boundary, n_vertical, n_horizontal):
    vert_ends = np.linspace(boundary['south'], boundary['north'], n_vertical+1)
    horz_ends = np.linspace(boundary['west'], boundary['east'], n_horizontal+1)
    vert_bounds = list(zip(vert_ends[:-1], vert_ends[1:]))
    horz_bounds = list(zip(horz_ends[:-1], horz_ends[1:]))
    return vert_bounds, horz_bounds

n_vertical = 2
n_horizontal = 4
with open('./utils/bounding_box.txt', 'r') as bbx_file:
    north, south, east, west = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

boundary = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
vert_bounds, horz_bounds = partition_area(boundary, n_vertical, n_horizontal)

results, errors = execute('python ground-map/ground_map.py --bounding_box_path ./utils/bounding_box.txt --ground_map_path ./ground-map/map/all_edges.shp --filtered_map_path ./ground-map/map/filtered_edges.shp --dropped_map_path ./ground-map/map/dropped_edges.shp')
results, errors = execute('python matching/match.py --ground_map_path ./ground-map/map/all_edges.shp --trajs_path ./data/trajectories/trajs.shp --output_file_path ./data/trajs_mr.csv --write_opath True --radius 100 --gps_error 40')
for vert_bound in vert_bounds:
    for horz_bound in horz_bounds:
        boundary = dict(
            east=horz_bound[1], west=horz_bound[0], north=vert_bound[1], south=vert_bound[0]
        )
        output_dir = f'{str(boundary["west"]).index(".")}{str(boundary["west"]).replace(".", "")}-' + \
             f'{str(boundary["west"]).index(".")}{str(boundary["east"]).replace(".", "")}-' + \
             f'{str(boundary["west"]).index(".")}{str(boundary["south"]).replace(".", "")}-' + \
             f'{str(boundary["west"]).index(".")}{str(boundary["north"]).replace(".", "")}'
        print(f'boundary {output_dir} started.')
        bb_path = f'bb_{output_dir}.txt'
        with open(f'./utils/{bb_path}', 'w') as bound_file:
            txt2write = f'NORTH_LATITUDE={boundary["north"]}\n'+\
            f'SOUTH_LATITUDE={boundary["south"]}\n'+\
            f'EAST_LONGITUDE={boundary["east"]}\n'+\
            f'WEST_LONGITUDE={boundary["west"]}'
            bound_file.write(txt2write)
        split_threshold = 50000
        trajs_dirpath = './data/gps-csv/sample-area/'
        csv_dirpath = './data/gps-csv/'
        _ = traj_partition(trajs_dirpath, boundary, csv_dirpath, split_threshold)
        groundmap_dir = os.path.join('./ground-map/map/', output_dir)
        csv_dirpath = os.path.join(csv_dirpath, output_dir)
        results_path = os.path.join('./results/kde/', output_dir)
        inference_path = os.path.join('./data/', output_dir)
        match_path = os.path.join('./data/', output_dir)
        results, errors = execute(f'python ground-map/ground_map.py --bounding_box_path ./utils/{bb_path} --ground_map_path {groundmap_dir}/all_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp')
        print('*'*50)
        results, errors = execute(f'python kde/kde.py --trajs_path {csv_dirpath} --kde_output_path {results_path}/kde.png --raw_output_path {results_path}/raw_data.png --bounding_box_path ./utils/{bb_path}')
        print('*' * 50)
        results, errors = execute(f'python kde/skeleton.py --input_image_file {results_path}/kde.png --output_image_file {results_path}/skeleton.png --output_skeleton_dir {results_path}/skeleton-images/ --closing_radius 6')
        print('*' * 50)
        results, errors = execute(f'python kde/graph_extract.py --skeleton_image_path {results_path}/skeleton.png --bounding_box_path ./utils/{bb_path} --output_file_path {results_path}/skeleton-maps/skeleton_map_1m.db')
        print('*' * 50)
        results, errors = execute(f'python edge_traj.py --map_dbpath {results_path}/skeleton-maps/skeleton_map_1m.db --shape_output_path {inference_path}/edges.shp --n_edge_splits 9 --min_length 20')
        print('*' * 50)
        results, errors = execute(f'python matching/match.py --ground_map_path {groundmap_dir}/filtered_edges.shp --trajs_path {inference_path}/edges.shp --add_score True --save_unmatched True --write_opath True --output_file_path {match_path}/mr.csv --radius 20 --gps_error 20 --n_edge_split 9 --overlap_portion 0.5')
        print('*' * 50)
        results, errors = execute(f'python matching/match.py --ground_map_path {groundmap_dir}/dropped_edges.shp --trajs_path {match_path}/unmatched.shp --add_score True --output_file_path {match_path}/unmatched_mr.csv --write_opath True --radius 60 --gps_error 40 --n_edge_split 9 --overlap_portion 0.33')
        print('*' * 50)
        results, errors = execute(f'python evaluation.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --results_save_path {results_path}/evaluation_results.txt')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/True_with_cs_dropped.png --apply_cos_sim True --background_map dropped')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/True_with_cs_filtered.png --apply_cos_sim True --background_map filtered')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/False_with_cs_dropped.png --apply_cos_sim True --false_edges True --background_map dropped')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/False_with_cs_filtered.png --apply_cos_sim True --false_edges True --background_map filtered')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/True_without_cs_dropped.png --background_map dropped')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/unmatched_dropped.png --plot_matches True --background_map dropped')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/unmatched_filtered.png --plot_matches True --background_map filtered')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/matched_dropped.png --background_map dropped')
        print('*' * 50)
        results, errors = execute(f'python plot.py --match_path {match_path}/mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path {inference_path}/edges.shp --dropped_map_path {groundmap_dir}/dropped_edges.shp --filtered_map_path {groundmap_dir}/filtered_edges.shp --figure_save_path {results_path}/all_filtered.png --plot_all_edges True --background_map filtered')
        print('*'*50)