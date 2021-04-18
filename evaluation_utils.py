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

def traj_partition(dirpath, boundary, output_dirpath, split_threshold):
    all_files = sorted(glob.glob(os.path.join(dirpath, "*.csv")))
    each_file_df = (pd.read_csv(f) for f in all_files)
    all_trajs = pd.concat(each_file_df, ignore_index=True)

    all_trajs = all_trajs[
        all_trajs.longitude.between(boundary['west'], boundary['east'], inclusive=True) & \
        all_trajs.latitude.between(boundary['south'], boundary['north'], inclusive=True)
        ]

    all_trajs.reset_index(drop=True, inplace=True)

    output_dir = f'{str(boundary["west"]).index(".")}{str(boundary["west"]).replace(".", "")}-' + \
                 f'{str(boundary["west"]).index(".")}{str(boundary["east"]).replace(".", "")}-' + \
                 f'{str(boundary["west"]).index(".")}{str(boundary["south"]).replace(".", "")}-' + \
                 f'{str(boundary["west"]).index(".")}{str(boundary["north"]).replace(".", "")}'


    output_dir = os.path.join(output_dirpath+output_dir, 'sample-area')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    split_parts = int(len(all_trajs) / min(split_threshold, len(all_trajs)))
    idxs = np.array_split(all_trajs, split_parts)
    start_idx = 0
    for df in idxs:
        end_idx = min(df.index[-1], len(all_trajs) - 2)
        while all_trajs.iloc[end_idx].route_id == all_trajs.iloc[end_idx + 1].route_id:
            end_idx += 1
            if end_idx + 1 == len(all_trajs):
                break
        file_name = os.path.join(output_dir, f'{start_idx}-{end_idx}.csv')
        chunk_df = all_trajs.iloc[start_idx:end_idx + 1]
        chunk_df.to_csv(file_name, sep=',', header=True, index=False)
        start_idx = end_idx + 1

    return output_dir