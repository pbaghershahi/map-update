from evaluation_utils import traj_partition

boundary = dict(east=51.3226, west=51.3093, north=35.7576, south=35.7470)
split_threshold = 50000
trajs_dirpath = './data/gps-csv/51513535/'
output_dirpath = './data/specific-areas/'
_ = traj_partition(trajs_dirpath, boundary, output_dirpath, split_threshold)

