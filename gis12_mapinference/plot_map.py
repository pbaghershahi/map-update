import matplotlib.pyplot as plt

with open('final_map.txt') as map_file:
    lines = map_file.readlines()
    i = 0
    while i <= len(lines) - 1:
        start_point = [float(x) for x in lines[i].strip('\n').split(',')]
        end_point = [float(x) for x in lines[i + 1].strip('\n').split(',')]
        i += 3
        plt.plot([start_point[1], end_point[1]], [start_point[0], end_point[0]])
plt.show()