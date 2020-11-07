import osmnx as ox
import geopandas as gp

north = 35.7417
south = 35.7340
east = 51.3520
west = 51.3430
graph = ox.graph_from_bbox(north, south, east, west, network_type='drive')
nodes, edges = ox.graph_to_gdfs(graph)
edges.columns = ['id', 'oneway', 'lanes', 'highway', 'maxspeed', 'length', 'geometry', 'bridge', 'name', 'ref', 'source', 'target', 'key']
new_df = edges[['id', 'source', 'target', 'geometry']]
new_df['id'] = new_df['id'].apply(lambda x: x[0] if type(x)==list else x)
print(new_df)

new_df.to_file('map/MyGeometries.shp')
df = gp.read_file('map/MyGeometries.shp')
print(df)
