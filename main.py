from fmm import GPSConfig,ResultConfig, Network,NetworkGraph,STMATCH,STMATCHConfig

config = STMATCHConfig()
config.k = 4
config.gps_error = 0.5
config.radius = 0.0002
config.vmax = 30;
config.factor =1.5

network = Network('ground-map/map/filtered_edges.shp')
graph = NetworkGraph(network)
print(graph.get_num_vertices())
model = STMATCH(network,graph)

input_config = GPSConfig()
input_config.file = './data/trajectories/trajs.shp'
# input_config.file = './test/data-test/trajectories/trajs.shp'
input_config.id = 'id'

print(input_config.to_string())
print('*'*20)

result_config = ResultConfig()
result_config.file = './data/mr.csv'
# result_config.file = './test/data-test/mr.csv'
result_config.output_config.write_opath = True
result_config.output_config.write_length = True
result_config.output_config.write_ep = True
result_config.output_config.write_tp = True
# result_config.output_config.write_ogeom = True
# result_config.output_config.write_offset = True
result_config.output_config.write_error = True

status = model.match_gps_file(input_config, result_config, config)

print('*'*20)
print(result_config.to_string())
print(status)