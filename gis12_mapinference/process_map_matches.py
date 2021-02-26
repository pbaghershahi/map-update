from streetmap import StreetMap
from pylibs import spatialfunclib
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import math
import seaborn as sn
import matplotlib.pyplot as plt

PRUNING_RMSE_THRESHOLD = 100

class ProcessMapMatches:
    def __init__(self):
        pass
    
    def process(self, graphdb_filename, matched_trips_directory, output_db_filename, output_traces_filename):
        all_segment_obs = self.process_all_matched_trips(graphdb_filename, matched_trips_directory, output_db_filename)
        self.coalesce_segments(output_db_filename, output_traces_filename, all_segment_obs)

    def process_all_matched_trips(self, graphdb_filename, matched_trips_directory, output_db_filename):
        self.graphdb = StreetMap()
        self.graphdb.load_graphdb(graphdb_filename)

        # all_matched_trip_files = [x for x in os.listdir(matched_trips_directory) if x.startswith("matched_trip_") and x.endswith(".txt")]

        all_segment_obs = {}  # indexed by segment_id
        # dict_of_keys = {}

        # distance_distros = []
        for dir_name in [x for x in os.listdir(matched_trips_directory) if
                         os.path.isdir(os.path.join(matched_trips_directory, x)) and not x.startswith('.')]:
            file_names = sorted(os.listdir(os.path.join(matched_trips_directory, dir_name)))

            for file_name in file_names:
                if not file_name.endswith('.csv'):
                    continue

                full_inputpath = os.path.join(matched_trips_directory, dir_name, file_name)

                if os.path.exists(full_inputpath) is not True:
                    print('Path does not exists!')
                    continue

                csv_file = open(full_inputpath)
                temp_trips = csv_file.readlines()
                csv_file.close()

                first, last = 0, 0
                for i in range(len(temp_trips) - 1):
                    curr_point = temp_trips[i].strip('\n').split(',')
                    next_point = temp_trips[i + 1].strip('\n').split(',')
                    last += 1
                    if curr_point[0] != next_point[0]:
                        if last - first >= 2:
                            matched_trip_records = [x.strip("\n").split(",") for x in temp_trips[first:last]]
                            # note: process each trips
                            # all_segment_obs = self.process_matched_trip(matched_trip_records, all_segment_obs, dict_of_keys)
                            self.process_matched_trip(matched_trip_records, all_segment_obs)
                            # for key, value in all_segment_obs.items():
                            #     print(key, len(value))
                            # print(len(dict_of_keys))
                        first = last

        #
        # At this point, we're done processing all map-matched trips
        #
        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")

        segment_counter = 1

        # print(dict_of_keys.keys() == all_segment_obs.keys())

        # clean up segment-matched traces
        counter = 0
        omit_counter = 0
        rmse_sum = 0
        for segment_id in all_segment_obs:
            # sys.stdout.write("\rPost-processing map-matched segment " + str(segment_counter) + "/" + str(len(all_segment_obs)) + "... ")
            # sys.stdout.flush()
            print("\rPost-processing map-matched segment " +
                  str(segment_counter) + "/" + str(len(all_segment_obs)) + "... ")

            segment_counter += 1

            good_segment_traces = []

            # print(len(all_segment_obs[segment_id]))
            for trace in all_segment_obs[segment_id]:

                trace_error = 0.0

                for obs in trace:
                    edge_id, obs_lat, obs_lon, obs_time = obs
                    edge = self.graphdb.edges[edge_id]

                    obs_lat = float(obs_lat)
                    obs_lon = float(obs_lon)

                    # sanity check
                    if edge not in self.graphdb.segments[segment_id].edges:
                        print("ERROR!! Edge (" + str(edge_id) + ") not in segment (" + str(
                            segment_id) + ") edge list!")
                        exit()

                    _, _, projected_dist = spatialfunclib.projection_onto_line(edge.in_node.latitude,
                                                                               edge.in_node.longitude,
                                                                               edge.out_node.latitude,
                                                                               edge.out_node.longitude, obs_lat,
                                                                               obs_lon)
                    trace_error += projected_dist ** 2
                    # distance_distros.append(projected_dist)

                trace_rmse = math.sqrt(float(trace_error) / float(len(trace)))

                counter += 1
                rmse_sum += trace_rmse
                if trace_rmse <= PRUNING_RMSE_THRESHOLD:
                    good_segment_traces.append(trace)
                else:
                    print('Weeeeeeeee from RMSE')
                    omit_counter += 1

                # print(trace_rmse, omit_counter, counter, omit_counter/counter, rmse_sum/counter)

            # print(len(good_segment_traces))
            all_segment_obs[segment_id] = good_segment_traces

        # sn.displot(distance_distros, bins=100)
        # plt.xlabel('projections distance (m)')
        # plt.show()

        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")

        # sys.stdout.write("Saving new map... ")
        # sys.stdout.flush()
        print("Saving new map... ")

        # note: create new dataset of the map
        try:
            os.remove(output_db_filename)
        except OSError:
            pass

        conn = sqlite3.connect(output_db_filename)
        cur = conn.cursor()

        cur.execute("CREATE TABLE nodes (id INTEGER, latitude FLOAT, longitude FLOAT, weight FLOAT)")
        cur.execute("CREATE TABLE edges (id INTEGER, in_node INTEGER, out_node INTEGER, weight FLOAT)")
        cur.execute("CREATE TABLE segments (id INTEGER, edge_ids TEXT)")
        cur.execute("CREATE TABLE intersections (node_id INTEGER)")
        conn.commit()

        valid_nodes = set()
        valid_intersections = set()
        not_enough_edges_num = 0
        after_edge_counter = 0

        # print(len(self.graphdb.edges))

        for segment_id in all_segment_obs:
            num_segment_traces = len(all_segment_obs[segment_id])

            if num_segment_traces > 1:
                segment = self.graphdb.segments[segment_id]

                cur.execute("INSERT INTO segments VALUES (" + str(segment.id) + ",'" + str(
                    [edge.id for edge in segment.edges]) + "')")

                for edge in segment.edges:
                    cur.execute(
                        "INSERT INTO edges VALUES (" + str(edge.id) + "," + str(edge.in_node.id) + "," + str(
                            edge.out_node.id) + "," + str(num_segment_traces) + ")")
                    after_edge_counter += 1
                    valid_nodes.add(edge.in_node)
                    valid_nodes.add(edge.out_node)

            # else:
            #     segment = self.graphdb.segments[segment_id]
            #     # segment = all_segment_obs[segment_id]
            #     not_enough_edges_num += len(segment.edges)
            #     print(f'Weeeeeeeeeee from insertion: {not_enough_edges_num}. number of segment_traces = {num_segment_traces}')

        for node in valid_nodes:
            cur.execute("INSERT INTO nodes VALUES (" + str(node.id) + "," + str(node.latitude) + "," + str(
                node.longitude) + "," + str(node.weight) + ")")

            if node.id in self.graphdb.intersections:
                cur.execute("INSERT INTO intersections VALUES (" + str(node.id) + ")")

        conn.commit()
        conn.close()
        # print(len(self.graphdb.edges), after_edge_counter)
        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")

        return all_segment_obs

    # note: for each trip consists of set of nodes, compute its matched edges and their subject segments
    def process_matched_trip(self, matched_trip_records, all_segment_obs):

        curr_trip_obs = []
        no_obs_time_ranges = []

        # note: the following loop retrieve the matched edges id from the edge lookup table by their
        #  start and end coordinates. It also stores the unknown matches time with a 30s time threshold
        #  before and after the observation time, this time interval will be used to prune edges
        #  in the next step.
        for record in matched_trip_records:
            if len(record) < 7:
                _, obs_lat, obs_lon, obs_time, unknown_state = record
                obs_time = datetime.strptime(obs_time[:19], '%Y-%m-%d %H:%M:%S')

                # observation blackout +/- 30 secconds of 'unknown' state observation time
                no_obs_time_ranges.append(
                    (obs_time - timedelta(seconds=int(30)), obs_time + timedelta(seconds=int(30))))

            else:
                _, obs_lat, obs_lon, obs_time, state_in_node_lat, state_in_node_lon, state_out_node_lat, state_out_node_lon = record
                obs_time = datetime.strptime(obs_time[:19], '%Y-%m-%d %H:%M:%S')
                curr_state_edge = self.graphdb.edge_coords_lookup_table[
                    (float(state_in_node_lat), float(state_in_node_lon)), (
                    float(state_out_node_lat), float(state_out_node_lon))]
                curr_trip_obs.append((curr_state_edge.id, obs_lat, obs_lon, obs_time))

        # note: here for all observed nodes that matched to one edge which is not unknown,
        #  we check if it is not in any unknown time intervals which are stored in no_obs_time_ranges,
        #  if so we just skip that observation.
        if len(no_obs_time_ranges) > 0:
            clean_trip_obs = []

            # skip observations that fall in the "no observations" time windows
            for trip_obs in curr_trip_obs:
                edge_id, obs_lat, obs_lon, obs_time = trip_obs

                skip_obs = False
                for no_obs_time_range in no_obs_time_ranges:
                    if no_obs_time_range[0] <= obs_time <= no_obs_time_range[1]:
                        skip_obs = True
                        break

                if skip_obs is False:
                    clean_trip_obs.append(trip_obs)
            # if len(clean_trip_obs) != len(curr_trip_obs):
            #     print(len(curr_trip_obs), len(clean_trip_obs))
            curr_trip_obs = clean_trip_obs

        prev_segment_id = None
        curr_segment_obs = None


        # print('new trip is processing!', len(curr_trip_obs))
        # ambiguity: it does not use the clean_trip_obs instead of curr_trip_obs. so why it is even created?
        for trip_obs in curr_trip_obs:
            # print(trip_obs)
            edge_id, obs_lat, obs_lon, obs_time = trip_obs

            curr_segment = self.graphdb.edges[edge_id].segment  # segment_lookup_table[edge_id]

            if curr_segment.id not in all_segment_obs:
                # print('segment id added')
                all_segment_obs[curr_segment.id] = []
            # else:
            #     print('segment id already exists')

            if curr_segment.id != prev_segment_id:
                if prev_segment_id is not None:
                    all_segment_obs[prev_segment_id].append(curr_segment_obs)
                    # print(len(all_segment_obs[prev_segment_id]))
                curr_segment_obs = []
            #
            # if curr_segment.id in dict_of_keys.keys():
            #     dict_of_keys[curr_segment.id] += 1
            # else:
            #     dict_of_keys[curr_segment.id] = 0
            # print(prev_segment_id, curr_segment.id, len(all_segment_obs[curr_segment.id]))
            curr_segment_obs.append((edge_id, obs_lat, obs_lon, obs_time))
            prev_segment_id = curr_segment.id

        if prev_segment_id is not None:
            all_segment_obs[prev_segment_id].append(curr_segment_obs)

        # for key, value in all_segment_obs.items():
        #     print(key, len(value))

        # return all_segment_obs
    
    def coalesce_segments(self, output_db_filename, output_traces_filename, all_segment_obs):
        self.graphdb = StreetMap()
        self.graphdb.load_graphdb(output_db_filename)

        # sys.stdout.write("Coalescing segments... ")
        # sys.stdout.flush()
        print("Coalescing segments... ")

        # for edge in list(self.graphdb.edges.values()):
        #     print(edge.in_node.coords(), edge.out_node.coords())

        while True:
            merge_segments = []

            for segment in list(self.graphdb.segments.values()):
                head_edge_neighbors = list(set(segment.head_edge.in_node.in_nodes + segment.head_edge.in_node.out_nodes))
                tail_edge_neighbors = list(set(segment.tail_edge.out_node.out_nodes + segment.tail_edge.out_node.in_nodes))

                if segment.head_edge.out_node in head_edge_neighbors:
                    head_edge_neighbors.remove(segment.head_edge.out_node)

                if segment.tail_edge.in_node in tail_edge_neighbors:
                    tail_edge_neighbors.remove(segment.tail_edge.in_node)

                if (len(head_edge_neighbors) != 1) and (len(tail_edge_neighbors) == 1):
                    edge_key = (segment.tail_edge.out_node, tail_edge_neighbors[0])

                    if edge_key in self.graphdb.edge_lookup_table:
                        next_edge = self.graphdb.edge_lookup_table[edge_key]
                        next_segment = next_edge.segment # self.graphdb.segment_lookup_table[next_edge.id]
                        merge_segments.append((segment, next_segment))

            #print "merge segments: " + str(len(merge_segments))
            if len(merge_segments) == 0:
                break

            for head_segment, tail_segment in merge_segments:
                head_segment.edges.extend(tail_segment.edges)

                for edge in tail_segment.edges:
                    edge.segment = head_segment #self.graphdb.segment_lookup_table[edge.id] = head_segment

                del self.graphdb.segments[tail_segment.id]


        # for edge in list(self.graphdb.edges.values()):
        #     print(edge.in_node.coords(), edge.out_node.coords())

        print("done.\n")
        print("Saving traces... ")
        
        output_traces_file = open(output_traces_filename, 'w')
        
        for segment_id in all_segment_obs:
            segment_traces = all_segment_obs[segment_id]
            
            if len(segment_traces) > 1:
                for segment_trace in segment_traces:
                    for obs in segment_trace:
                        edge_id, obs_lat, obs_lon, obs_time = obs
                        curr_segment_id = self.graphdb.edges[edge_id].segment.id
                        output_traces_file.write(str(curr_segment_id) + "," + str(edge_id) + "," + str(obs_lat) + "," + str(obs_lon) + "," + str(obs_time) + "\n")
                    output_traces_file.write("\n")
        output_traces_file.close()
        
        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")
        
        # sys.stdout.write("Saving coalesced map... ")
        # sys.stdout.flush()
        print("Saving coalesced map... ")
        
        try:
            os.remove(output_db_filename)
        except OSError:
            pass
        
        conn = sqlite3.connect(output_db_filename)
        cur = conn.cursor()
        
        cur.execute("CREATE TABLE nodes (id INTEGER, latitude FLOAT, longitude FLOAT, weight FLOAT)")
        cur.execute("CREATE TABLE edges (id INTEGER, in_node INTEGER, out_node INTEGER, weight FLOAT)")
        cur.execute("CREATE TABLE segments (id INTEGER, edge_ids TEXT)")
        cur.execute("CREATE TABLE intersections (node_id INTEGER)")
        conn.commit()
        
        valid_nodes = set()
        valid_intersections = set()
        
        for segment in list(self.graphdb.segments.values()):
            cur.execute("INSERT INTO segments VALUES (" + str(segment.id) + ",'" + str([edge.id for edge in segment.edges]) + "')")
            
            segment_weight = min([edge.weight for edge in segment.edges])
            #print map(lambda edge: edge.weight, segment.edges), min(map(lambda edge: edge.weight, segment.edges))
            
            for edge in segment.edges:
                cur.execute("INSERT INTO edges VALUES (" + str(edge.id) + "," + str(edge.in_node.id) + "," + str(edge.out_node.id) + "," + str(segment_weight) + ")")
                
                valid_nodes.add(edge.in_node)
                valid_nodes.add(edge.out_node)
        
        for node in valid_nodes:
            cur.execute("INSERT INTO nodes VALUES (" + str(node.id) + "," + str(node.latitude) + "," + str(node.longitude) + "," + str(node.weight) + ")")
            
            if node.id in self.graphdb.intersections:
                cur.execute("INSERT INTO intersections VALUES (" + str(node.id) + ")")
        
        conn.commit()
        conn.close()
        
        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")


import sys, getopt
import os
if __name__ == '__main__':
    graphdb_filename = "skeleton_maps/skeleton_map_7m.db"
    matched_trips_directory = "trips/matched_trips_7m/"
    output_filename = "skeleton_maps/skeleton_map_7m_mm1.db"

    opts, args = getopt.getopt(sys.argv[1:],"d:t:o:h")
    
    for o, a in opts:
        if o == "-d":
            graphdb_filename = str(a)
        elif o == "-t":
            matched_trips_directory = str(a)
        elif o == "-o":
            output_filename = str(a)
        elif o == "-h":
            print("Usage: python process_map_matches.py [-d <graphdb_filename>] [-t <matched_trips_directory>] [-o <output_filename>] [-h]")
            exit()
    
    print("graphdb filename: " + str(graphdb_filename))
    print("matched trips directory: " + str(matched_trips_directory))
    print("output filename: " + str(output_filename))
    
    p = ProcessMapMatches()
    p.process(graphdb_filename, matched_trips_directory, output_filename, output_filename.replace(".db","_traces.txt"))
