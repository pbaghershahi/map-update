import os
import pandas as pd

class Location:
    def __init__(self, id, latitude, longitude, time):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.time = time
    
    def __str__(self):
        return str(self.id) + "," + str(self.latitude) + "," + str(self.longitude) + "," + str(self.time)

class Trip:
    def __init__(self):
        self.locations = []
    
    def add_location(self, location):
        self.locations.append(location)
    
    @property
    def num_locations(self):
        return len(self.locations)
    
    @property
    def start_time(self):
        return self.locations[0].time
    
    @property
    def end_time(self):
        return self.locations[-1].time
    
    @property
    def duration(self):
        return self.end_time - self.start_time

class TripLoader:
    
    @staticmethod
    def load_all_trips(trips_path):
        
        # storage for all trips
        trajectories = []
        
        # iterate through all trip filenames
        # for trip_filename in os.listdir(trips_path):
        for dir_name in [x for x in os.listdir(trips_path) if os.path.isdir(os.path.join(trips_path, x)) and not x.startswith('.')]:
            file_names = sorted(os.listdir(os.path.join(trips_path, dir_name)))

            # if filename starts with "trip_"
            # if trip_filename.startswith("part-") is True:
            for file_name in file_names:
                if not file_name.endswith('.csv'):
                    continue

                # load trip from file
                # new_trip = TripLoader.load_trip_from_file(trips_path + "/" + trip_filename)
                modified_trips = TripLoader.load_trip_from_file(os.path.join(trips_path, dir_name, file_name))
                trajectories += modified_trips
        
        # return all trips
        return trajectories
    
    @staticmethod
    def load_trip_from_file(trip_filename):

        # open trip file
        if os.path.exists(trip_filename) is not True:
            print('Path does not exists!')
            return

        # create new trip object
        new_trip = Trip()
        temp_trips = pd.read_csv(trip_filename, sep=',', header=0, engine='python')
        modified_trips = []
        for i in range(len(temp_trips) - 1):
            point = temp_trips.iloc[i]
            new_trip.add_location(
                Location(
                    str(point['route_id']),
                    float(point['latitude']),
                    float(point['longitude']),
                    str(point['timestamp'])
                )
            )
            if point['route_id'] != temp_trips.iloc[i + 1]['route_id']:
                if len(new_trip.locations) >= 2:
                    modified_trips.append(new_trip)
                new_trip = Trip()

        return modified_trips


class TripWriter:
    
    @staticmethod
    def write_trip_to_file(trip, trip_id, trips_path):

        if not os.path.exists(trips_path):
            os.mkdir(trips_path)

        with open(trips_path + "/trip_" + str(trip_id) + ".txt", 'w') as trip_file:
            for trip_location in trip.locations:
                trip_file.write(str(trip_location) + "\n")
