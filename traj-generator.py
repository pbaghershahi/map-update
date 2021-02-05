from filtering import load_data, trajToShape

# north = 35.7417
# south = 35.7340
# east = 51.3520
# west = 51.3430

north = 35.7587
south = 35.7460
east = 51.3224
west = 51.3042

files_path = './data'
# files_path = './test/data-test'
boundary = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
trajs = load_data(files_path, boundary, './data/gps-csv')
# trajs = load_data(files_path, boundary, './test/data-test/gps-csv')

# trajToShape('./test/data-test/gps-csv', './test/data-test/trajectories/trajs.shp')
trajToShape('./data/gps-csv', './data/trajectories/trajs.shp')
