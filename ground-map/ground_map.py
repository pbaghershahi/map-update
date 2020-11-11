import osmnx as ox
import geopandas as gp

north = 35.7417
south = 35.7340
east = 51.3520
west = 51.3430
graph = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False, retain_all=True)
nodes, edges = ox.graph_to_gdfs(graph)
# edges.columns = ['id', 'bridge', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'length', 'lanes', 'geometry', 'source', 'target', 'key']
edges.columns = ['osmid', 'bridge', 'oneway', 'ref', 'name', 'highway', 'maxspeed', 'length', 'lanes', 'geometry', 'source', 'target', 'key']
edges['id'] = range(len(edges))
new_df = edges[['id', 'source', 'target', 'geometry']]
new_df['id'] = new_df['id'].apply(lambda x: x[0] if type(x)==list else x)
print(new_df)

new_df.to_file('./map/edges.shp')
df = gp.read_file('./map/edges.shp')
print(df)
