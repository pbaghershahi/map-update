import pandas as pd
import numpy as np
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

north = 35.7417
south = 35.7340
east = 51.3520
west = 51.3430
area = ox.geometries_from_bbox(north, south, east, west, tags={'highway':True})
new_area = area[['unique_id', 'osmid', 'element_type', 'geometry']]
new_area[(new_area['element_type'] == 'way')].to_file('MyGeometries.shp', driver='ESRI Shapefile')