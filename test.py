from fmm import Network,NetworkGraph,STMATCH,STMATCHConfig
network = Network("ground-map/map/edges.shp")
graph = NetworkGraph(network)
print(graph.get_num_vertices())
model = STMATCH(network,graph)
wkt = "LINESTRING (51.34698 35.738228, 51.34705 35.73839, 51.347088 35.738453, 51.347088 35.738453, 51.347095 35.738464)"
config = STMATCHConfig()
config.k = 4
config.gps_error = 0.5
config.radius = 0.4
config.vmax = 30;
config.factor =1.5
result = model.match_wkt(wkt,config)
print(type(result))
print("Opath ",list(result.opath))
print("Cpath ",list(result.cpath))
print("Indices ",list(result.indices))
print("WKT ",result.mgeom.export_wkt())
# print(dir(next(iter(result.candidates))))
for c in result.candidates:
    print(c.edge_id, c.index)
