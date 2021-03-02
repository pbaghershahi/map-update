from graphdb_matcher import GraphDBMatcher
import spatialfunclib
import math, csv
import pandas as pd
from datetime import datetime, timedelta

# ambiguity: difference between this threshold and the one in graphdb_matcher is ambiguous
max_viterbi_subdivision = 10.0

class MatchGraphDB:
    def __init__(self, graphdb_filename, constraint_length, max_dist):
        self.matcher = GraphDBMatcher(graphdb_filename, constraint_length, max_dist)
        self.constraint_length = constraint_length

    def process_trip(self, trips, csv_writer):

        # note: V is the viterbi matrix. It is a dictionary with
        #  nodes as key of type (latitude, longitude) and viterbi probability as value
        V = None
        # note: p is dictionary to store path
        p = {}

        # note: obs is a list to add all actual observed nodes on the trip so each element
        #  of the list is in the form (id, lat, lon, time)
        obs = []
        # note: obs_states is a list to add all matched edges of the observed nodes on the trip
        #  so element of the list is in the form (edge_start_lat, edge_start_lon, edge_end_lat, edge_end_lon)
        obs_states = []
        max_prob_p = None

        first_obs = trips.iloc[0]
        first_obs_id = first_obs['route_id']
        first_obs_lat = first_obs['latitude']
        first_obs_lon = first_obs['longitude']
        first_obs_time = first_obs['timestamp']

        # note: matcher computes viterbi matrix for each transition.
        V, p = self.matcher.step((float(first_obs_lat), float(first_obs_lon)), V, p)

        max_prob_state = max(V, key=lambda x: V[x])
        max_prob_p = p[max_prob_state]

        if len(max_prob_p) == self.constraint_length:
            print(max_prob_p[0])
            obs_states.append(max_prob_p[0])

        obs.append((first_obs_id, first_obs_lat, first_obs_lon, first_obs_time))

        # note: the following loop first adds each point on the trips to the observation list (obs)
        #  then checks the distance between each two pair of them coming continuously after each other
        #  if the distance is greater than 10m then it breaks the distance two smaller parts and
        #  call the matcher function on each existing or created middle points which returns the viterbi
        #  to this current node and the path based on the viterbi to the current node. Then each time
        #  for each node it checks if the length of the path is grater than the maximum length
        #  it just adds the start of the path to the observations states list (obs_states) because
        #  in the viterbi matrix and the according path, each node has the history of the previous nodes
        #  and the loop also checks the mentioned condition each time a new node observes from the path,
        #  so we should just add the first node of the path and finally just add the path to the
        #  last node on the trip which returns the most probable path so every time for each two continuous
        #  points in the checking distance loop and the main loop of the trip we just check the length condition
        #  and do not add any path to the obs_states list, then after the main loop pf the trips ends, we just
        #  add the path to the last point of the trips which should be in the same length of the all observed
        #  nodes on the trip.

        for i in range(1, len(trips)):
            prev_point, curr_point = trips.iloc[i-1], trips.iloc[i]
            prev_lat, prev_lon = prev_point['latitude'], prev_point['longitude']
            prev_time = datetime.strptime(prev_point['timestamp'][:19], '%Y-%m-%d %H:%M:%S')
            curr_lat, curr_lon = curr_point['latitude'], curr_point['longitude']
            curr_time = datetime.strptime(curr_point['timestamp'][:19], '%Y-%m-%d %H:%M:%S')

            elapsed_time = (curr_time - prev_time).seconds

            distance = spatialfunclib.distance((float(prev_lat), float(prev_lon)), (float(curr_lat), float(curr_lon)))

            # note: divide distances greater than maximum distance
            #  to subparts of 10 m to calculate viterbi probability and path
            if distance > max_viterbi_subdivision:
                int_steps = int(math.ceil(distance / max_viterbi_subdivision))
                int_step_distance = (distance / float(int_steps))
                int_step_time = (float(elapsed_time) / float(int_steps))

                for j in range(1, int_steps):
                    step_fraction_along = (j * int_step_distance) / distance
                    int_step_lat, int_step_lon = spatialfunclib.point_along_line(float(prev_lat), float(prev_lon), float(curr_lat), float(curr_lon), step_fraction_along)

                    V, p = self.matcher.step((float(int_step_lat), float(int_step_lon)), V, p)

                    max_prob_state = max(V, key=lambda x: V[x])
                    max_prob_p = p[max_prob_state]

                    if len(max_prob_p) == self.constraint_length:
                        obs_states.append(max_prob_p[0])

                    obs.append((curr_point['route_id'], int_step_lat, int_step_lon, prev_time + timedelta(seconds=int(j*int_step_time))))

            V, p = self.matcher.step((float(curr_lat), float(curr_lon)), V, p)

            max_prob_state = max(V, key=lambda x: V[x])
            max_prob_p = p[max_prob_state]

            if len(max_prob_p) == self.constraint_length:
                obs_states.append(max_prob_p[0])

            obs.append((curr_point['route_id'], curr_lat, curr_lon, curr_time))

        if len(max_prob_p) < self.constraint_length:
            obs_states.extend(max_prob_p)
        else:
            # note: there is no way that max_prob_p be greater than the constraint length, because
            #  the viterbi algorithm just cut the sentences length to the constraint length itself
            #  by popping from the beginning of the path. Also pay attention that whenever
            #  len(max_prob_p) = constraint_length we have already add the first state in the main loop.
            obs_states.extend(max_prob_p[1:])

        assert(len(obs_states) == len(obs))

        for i in range(0, len(obs)):
            row = list(obs[i])
            if obs_states[i] == "unknown":
                row += ['unknown']
            else:
                row += [obs_states[i][0][0], obs_states[i][0][1], obs_states[i][1][0], obs_states[i][1][1]]

            csv_writer.writerow(row)

import os
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Matching trajectories with extracted graph using Viterbi algorithm')
    parser.add_argument('--input_graph_file', type=str, help='Path to graph sqlite database file')
    parser.add_argument('--trajs_path', type=str, help='Path to gps trajectories')
    parser.add_argument('--match_output_path', type=str, help='Directory to save matched trajectories')
    parser.add_argument('--max_v_length', type=float, default=300,
                        help='Maximum length to extend paths in viterbi algorithm')
    parser.add_argument('--max_r_dist', type=float, default=500,
                        help='Maximum distance to detect nearby areas in Rtree algorithm (areas are representations of map edges)')
    parser.add_argument('--max_division_dist', type=float, default=10.0,
                        help='Maximum distance to devide edges in Viterbi algorithm (unit: meters)')
    args = parser.parse_args()
    
    graphdb_filename = args.input_graph_file
    constraint_length = args.max_v_length
    max_dist = args.max_r_dist
    trip_directory = args.trajs_path
    output_directory = args.match_output_path
    max_viterbi_subdivision = args.max_division_dist
    
    print("constraint length: " + str(constraint_length))
    print("max dist: " + str(max_dist))
    print("graphdb filename: " + str(graphdb_filename))
    print("trip directory: " + str(trip_directory))
    print("output directory: " + str(output_directory))
    
    match_graphdb = MatchGraphDB(graphdb_filename, constraint_length, max_dist)

    for dir_name in [x for x in os.listdir(trip_directory) if os.path.isdir(os.path.join(trip_directory, x)) and not x.startswith('.')]:
        if not os.path.exists(os.path.join(output_directory, dir_name)):
            os.makedirs(os.path.join(output_directory, dir_name))
        file_names = sorted(os.listdir(os.path.join(trip_directory, dir_name)))


        for file_name in file_names:
            if not file_name.endswith('.csv'):
                continue

            full_inputpath = os.path.join(trip_directory, dir_name, file_name)
            full_outputpath = os.path.join(output_directory, dir_name, file_name)
            if os.path.exists(full_inputpath) is not True:
                print('Path does not exists!')
                continue
            temp_trips = pd.read_csv(full_inputpath, sep=',', header=0, engine='python')
            with open(full_outputpath, 'w') as csv_file:
                print(full_outputpath)
                first, last = 0, 0
                csv_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n')
                for i in range(len(temp_trips) - 1):
                    point = temp_trips.iloc[i]
                    last += 1
                    if point['route_id'] != temp_trips.iloc[i + 1]['route_id']:
                        if last-first >= 2:
                            match_graphdb.process_trip(temp_trips.iloc[first:last], csv_writer)

                        first = last
    print("done.\n")
