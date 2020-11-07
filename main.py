from filtering import load_data, make_traj_matrix
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

files_path = './data/'
boundry = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
trajs = load_data(files_path, boundry, './data/gps-csv')
trajs = make_traj_matrix(trajs)

# for line in trajs:
#     print(line)

df = pd.DataFrame(trajs, columns=['id', 'geometry'])
df = gp.GeoDataFrame(df, geometry='geometry')
df.to_file('MyGeometries.shp', driver='ESRI Shapefile')
