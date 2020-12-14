from filtering import load_data, trajToShape
import numpy as np
import pandas as pd
import geopandas as gp

north = 35.7417
south = 35.7340
east = 51.3520
west = 51.3430

# graph = ox.graph_from_bbox(north, south, east, west, network_type='drive')
# area = ox.geometries_from_bbox(north, south, east, west, tags={'highway':True})
# area.plot()

# files_path = './data'
files_path = './data-test'
boundary = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
# trajs = load_data(files_path, boundary, './data/gps-csv')
trajs = load_data(files_path, boundary, './data-test/gps-csv')

trajToShape('./data-test/gps-csv', './data-test/trajectories/trajs.shp')
# trajToShape('./data/gps-csv', './data/trajectories/trajs.shp')

# for line in trajs:
#     print(line)

# df = pd.DataFrame(trajs, columns=['id', 'geometry'])
# df = gp.GeoDataFrame(df, geometry='geometry')
# # df.to_file('./data/trajectories/trajs.shp', driver='ESRI Shapefile')
# df.to_file('./data-test/trajectories/trajs.shp', driver='ESRI Shapefile')
