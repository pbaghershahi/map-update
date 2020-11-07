from fmm import GPSConfig,ResultConfig, Network,NetworkGraph,STMATCH,STMATCHConfig

config = STMATCHConfig()
config.k = 4
config.gps_error = 0.5
config.radius = 0.4
config.vmax = 30;
config.factor =1.5

network = Network('ground-map/map/MyGeometries.shp')
graph = NetworkGraph(network)
print(graph.get_num_vertices())
model = STMATCH(network,graph)

input_config = GPSConfig()
input_config.file = './data/trajectories/MyGeometries.shp'
input_config.id = 'id'

print(input_config.to_string())
print('*'*20)

result_config = ResultConfig()
result_config.file = './data/mr.txt'
result_config.output_config.write_opath = True
result_config.output_config.write_length = True
status = model.match_gps_file(input_config, result_config, config)
print(result_config.to_string())