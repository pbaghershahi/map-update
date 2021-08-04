import geopandas as gp
import matplotlib.pyplot as plt


filtered_edges = gp.read_file('../ground-map/map/filtered_edges.shp')
filtered_edges.set_index('id', drop=True, inplace=True)

filtered_edges.plot()

with open('../results/kde/final_map.txt') as map_file:
    lines = map_file.readlines()
    i = 0
    while i <= len(lines) - 1:
        start_point = [float(x) for x in lines[i].strip('\n').split(',')]
        end_point = [float(x) for x in lines[i + 1].strip('\n').split(',')]
        i += 3
        plt.plot([start_point[1], end_point[1]], [start_point[0], end_point[0]], c='r')


# all_edges = gp.read_file('../ground-map/map/all_edges.shp')
# all_edges.set_index('id', drop=True, inplace=True)
#
# all_edges.plot()

plt.show()

