import pandas as pd
import datetime
import seaborn as sn
import matplotlib.pyplot as plt
import numpy as np
from shapely import wkb



sample_file = 'data/gps-data/part-00001-498c167d-fb29-4098-a9f9-682631b98b93-c000.snappy'
all_data = pd.read_parquet(sample_file)

########################## time interval distribution plot ############################
intervals = []
temp_times = []
# for i in range(len(all_data)-1):
for i in range(5000):
    print(datetime.datetime.fromtimestamp(int(all_data.iloc[i]['timestamp'])/1000))
    temp_times.append(datetime.datetime.fromtimestamp(int(all_data.iloc[i]['timestamp'])/1000))
    if all_data.iloc[i]['route_slug'] != all_data.iloc[i+1]['route_slug']:
        temp_times = sorted(temp_times)
        temp_times = [(temp_times[i+1]-temp_times[i]).seconds for i in range(len(temp_times)-1)]
        intervals += temp_times
        temp_times = []

sn.displot(intervals, color='r')
plt.xlabel('time intervals')
plt.savefig('time distribution')
# ===> time threshold = 20 s

########################### ditance interval distribution plot #############################

METERS_PER_DEGREE_LATITUDE = 111070.34306591158
METERS_PER_DEGREE_LONGITUDE = 83044.98918812413

dists = []
temp_trip = []
dist_measure = lambda x, y: np.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)
# for i in range(len(all_data)-1):
for i in range(20000):
    point = wkb.loads(all_data.iloc[i]['location'], hex=True)
    temp_trip.append([
        point.x*METERS_PER_DEGREE_LONGITUDE,
        point.y*METERS_PER_DEGREE_LATITUDE,
        datetime.datetime.fromtimestamp(int(all_data.iloc[i]['timestamp'])/1000)
    ])
    if all_data.iloc[i]['route_slug'] != all_data.iloc[i+1]['route_slug']:
        temp_trip = sorted(temp_trip, key=lambda x: x[2])
        temp_trip = [
            dist_measure(temp_trip[i], temp_trip[i+1]) for i in range(len(temp_trip)-1)
        ]
        dists += temp_trip
        temp_trip = []

sn.displot(dists)
plt.xlabel('distance intervals')
plt.savefig('distance distribution')

bin_values, edges = np.histogram(dists, bins=300)
bin_cum = np.cumsum(bin_values)
bin_cum = bin_cum/bin_cum[-1]
threshold = int(edges[np.argmin(abs(bin_cum-0.15))+1])

########################### speed interval distribution plot #################################

velocities = []
temp_trip = []
vel_measure = lambda x, y: np.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)/max((y[2]-x[2]).seconds, 1)# for i in range(len(all_data)-1):
for i in range(20000):
    point = wkb.loads(all_data.iloc[i]['location'], hex=True)
    temp_trip.append([
        point.x*83044.98918812413,
        point.y*111070.34306591158,
        datetime.datetime.fromtimestamp(int(all_data.iloc[i]['timestamp'])/1000)
    ])
    if all_data.iloc[i]['route_slug'] != all_data.iloc[i+1]['route_slug']:
        temp_trip = sorted(temp_trip, key=lambda x: x[2])
        temp_trip = [
            vel_measure(temp_trip[i], temp_trip[i+1]) for i in range(len(temp_trip)-1)
        ]
        velocities += temp_trip
        temp_trip = []

sn.displot(velocities, color='g')
plt.xlabel('average speed')
plt.savefig('average speed distribution')

bin_values, edges = np.histogram(velocities, bins=300)
bin_cum = np.cumsum(bin_values)
bin_cum = bin_cum/bin_cum[-1]
threshold = int(edges[np.argmin(abs(bin_cum-0.1))+1])