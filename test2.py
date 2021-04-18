import pandas as pd
import geopandas as gp
import matplotlib.pyplot as plt

filtered_edges = gp.read_file('./ground-map/map/all_edges.shp')
filtered_edges.set_index('id', drop=True, inplace=True)
filtered_edges.plot()

plt.show()