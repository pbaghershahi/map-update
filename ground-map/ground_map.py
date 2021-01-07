import osmnx as ox
import geopandas as gp
import numpy as np

# north = 35.7417
# south = 35.7340
# east = 51.3520
# west = 51.3430

north = 35.7587
south = 35.7460
east = 51.3224
west = 51.3042

graph = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False, retain_all=True)
nodes, edges = ox.graph_to_gdfs(graph)
print(edges.columns)
# edges.columns = ['osmid', 'bridge', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'length', 'lanes', 'geometry', 'source', 'target', 'key']
edges.columns = ['osmid', 'oneway', 'highway', 'length', 'ref', 'name', 'maxspeed', 'lanes', 'bridge', 'junction', 'geometry', 'source', 'target', 'key']
r_percent = 0.2
drop_indices = np.random.choice(edges[(edges.highway == 'residential')].index, int(r_percent*len(edges)), replace=False)
edges['id'] = range(len(edges))
all_edges = edges[['id', 'source', 'target', 'geometry']]
all_edges['id'] = all_edges['id'].apply(lambda x: x[0] if type(x) == list else x)
filtered_edges = all_edges.drop(drop_indices)
all_edges.to_file('./map/all_edges.shp')
df = gp.read_file('./map/all_edges.shp')
print(df)
filtered_edges.to_file('./map/filtered_edges.shp')
df = gp.read_file('./map/filtered_edges.shp')
print(df)