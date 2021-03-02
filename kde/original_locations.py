import os

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

        all_trips = []
        for trip_filename in os.listdir(trips_path):
            if trip_filename.startswith("trip_") is True:
                new_trip = TripLoader.load_trip_from_file(trips_path + "/" + trip_filename)
                if len(new_trip.locations) >= 2:
                    all_trips.append(new_trip)

        return all_trips
    
    @staticmethod
    def load_trip_from_file(trip_filename):

        new_trip = Trip()
        trip_file = open(trip_filename, 'r')
        for trip_location in trip_file:
            location_elements = trip_location.strip('\n').split(',')
            new_trip.add_location(
                Location(
                    str(location_elements[0]),
                    float(location_elements[1]),
                    float(location_elements[2]),
                    float(location_elements[3])
                )
            )
        trip_file.close()

        return new_trip

class TripWriter:
    
    @staticmethod
    def write_trip_to_file(trip, trip_id, trips_path):
        if not os.path.exists(trips_path):
            os.mkdir(trips_path)

        trip_file = open(trips_path + "/trip_" + str(trip_id) + ".txt", 'w')
        for trip_location in trip.locations:
            trip_file.write(str(trip_location) + "\n")
        trip_file.close()
