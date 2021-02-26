from filtering import load_data, trajToShape

# north = 35.7417
# south = 35.7340
# east = 51.3520
# west = 51.3430

north = 35.7630
south = 35.7407
east = 51.3392
west = 51.2891

files_path = './data'
# files_path = './test/data-test'
boundary = dict(
    east=east,
    west=west,
    north=north,
    south=south
)
# trajs = load_data(files_path, boundary, './data/gps-csv')

trajToShape('./data/gps-csv', './data/trajectories/trajs.shp')
