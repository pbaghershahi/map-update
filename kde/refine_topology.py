from streetmap import StreetMap, Node
from pylibs import spatialfunclib
import sqlite3
import math

class RefineTopology:
    def __init__(self, graphdb_filename):
        self.graphdb = StreetMap()
        self.graphdb.load_graphdb(graphdb_filename)

    # fixme: all deletes are passed to try and except, check if is it correct?
    def process(self, matched_traces_filename, output_db_filename):
        print("Loading matched traces... ")

        matched_traces_file = open(matched_traces_filename, 'r')

        all_segment_obs = {}
        
        prev_segment_id = None
        curr_segment_obs = None
        
        for obs in matched_traces_file:
            if obs == "\n":
                if prev_segment_id is not None:
                    all_segment_obs[prev_segment_id].append(curr_segment_obs)
                curr_segment_obs = []
                prev_segment_id = None
            
            else:
                segment_id, edge_id, obs_lat, obs_lon, obs_time = obs.strip("\n").split(",")
                curr_segment_id = int(segment_id)

                if curr_segment_id not in all_segment_obs:
                    all_segment_obs[curr_segment_id] = []
                
                if curr_segment_id != prev_segment_id:
                    if prev_segment_id is not None:
                        all_segment_obs[prev_segment_id].append(curr_segment_obs)
                    curr_segment_obs = []
                
                curr_segment_obs.append((edge_id, obs_lat, obs_lon, obs_time))
                prev_segment_id = curr_segment_id
        
        matched_traces_file.close()
        print("done.\n")
        print("Refining intersections... ")
        
        node_id = max(self.graphdb.nodes.keys()) + 1
        
        closed_segments_list = []
        
        while True:
            candidate_segments = []
            
            for segment in list(self.graphdb.segments.values()):
                if segment not in closed_segments_list:
                    segment_length = sum([edge.length for edge in segment.edges])
                    
                    if segment_length <= 50:
                        candidate_segments.append((segment, segment_length))
            
            if len(candidate_segments) < 1:
                break
            
            else:
                candidate_segments.sort(key=lambda x: x[1])
                segment = candidate_segments[0][0]
                touched_edges = []
                
                segment_head_node = segment.head_edge.in_node
                segment_tail_node = segment.tail_edge.out_node
                
                new_intersection_latitude = (segment_head_node.latitude + segment_tail_node.latitude) / 2.0
                new_intersection_longitude = (segment_head_node.longitude + segment_tail_node.longitude) / 2.0
                new_intersection_weight = (segment_head_node.weight + segment_tail_node.weight) / 2.0
                
                new_intersection = Node(new_intersection_latitude, new_intersection_longitude, node_id, new_intersection_weight)
                self.graphdb.nodes[node_id] = new_intersection
                node_id += 1
                
                print("new intersection: " + str(new_intersection.id))
                
                new_intersection.in_nodes.extend(segment_head_node.in_nodes)
                new_intersection.in_nodes.extend(segment_tail_node.in_nodes)

                if segment_head_node in new_intersection.in_nodes: new_intersection.in_nodes.remove(segment_head_node)
                if segment_tail_node in new_intersection.in_nodes: new_intersection.in_nodes.remove(segment_tail_node)
                
                new_intersection.out_nodes.extend(segment_head_node.out_nodes)
                new_intersection.out_nodes.extend(segment_tail_node.out_nodes)
                
                if segment_head_node in new_intersection.out_nodes: new_intersection.out_nodes.remove(segment_head_node)
                if segment_tail_node in new_intersection.out_nodes: new_intersection.out_nodes.remove(segment_tail_node)
                
                new_intersection.in_nodes = list(set(new_intersection.in_nodes))
                new_intersection.out_nodes = list(set(new_intersection.out_nodes))
                
                head_edge_neighbors = list(set(segment_head_node.in_nodes + segment_head_node.out_nodes))
                tail_edge_neighbors = list(set(segment_tail_node.out_nodes + segment_tail_node.in_nodes))                
                
                if segment.head_edge.out_node in head_edge_neighbors:
                    head_edge_neighbors.remove(segment.head_edge.out_node)
                
                if segment.tail_edge.in_node in tail_edge_neighbors:
                    tail_edge_neighbors.remove(segment.tail_edge.in_node)
                
                for neighbor in head_edge_neighbors:
                    if segment_head_node in neighbor.out_nodes:
                        edge_key = (neighbor, segment_head_node)
                        edge = self.graphdb.edge_lookup_table[edge_key]
                        
                        edge.out_node = new_intersection
                        print("adding key " + str((neighbor.id, new_intersection.id)) + ": " + str((neighbor, new_intersection)) + " = " + str(edge))
                        self.graphdb.edge_lookup_table[(neighbor, new_intersection)] = edge
                        try:
                            del self.graphdb.edge_lookup_table[edge_key]
                        except:
                            print(f'Edge key {edge_key} does not exists already!')
                        
                        neighbor.out_nodes.remove(segment_head_node)
                        neighbor.out_nodes.append(new_intersection)
                        
                        edge.old_key = edge_key
                        touched_edges.append(edge)
                    
                    if segment_head_node in neighbor.in_nodes:
                        edge_key = (segment_head_node, neighbor)
                        edge = self.graphdb.edge_lookup_table[edge_key]
                        
                        edge.in_node = new_intersection
                        print("adding key " + str((new_intersection.id, neighbor.id)) + ": " + str((new_intersection, neighbor)) + " = " + str(edge))
                        self.graphdb.edge_lookup_table[(new_intersection, neighbor)] = edge
                        try:
                            del self.graphdb.edge_lookup_table[edge_key]
                        except:
                            print(f'Edge key {edge_key} does not exists already!')
                        
                        neighbor.in_nodes.remove(segment_head_node)
                        neighbor.in_nodes.append(new_intersection)
                        
                        edge.old_key = edge_key
                        touched_edges.append(edge)
                
                for neighbor in tail_edge_neighbors:
                    if segment_tail_node in neighbor.out_nodes:
                        edge_key = (neighbor, segment_tail_node)
                        edge = self.graphdb.edge_lookup_table[edge_key]
                        
                        edge.out_node = new_intersection
                        print("adding key " + str((neighbor.id, new_intersection.id)) + ": " + str((neighbor, new_intersection)) + " = " + str(edge))
                        self.graphdb.edge_lookup_table[(neighbor, new_intersection)] = edge
                        try:
                            del self.graphdb.edge_lookup_table[edge_key]
                        except:
                            print(f'Edge key {edge_key} does not exists already!')
                        
                        neighbor.out_nodes.remove(segment_tail_node)
                        neighbor.out_nodes.append(new_intersection)
                        
                        edge.old_key = edge_key
                        touched_edges.append(edge)
                    
                    if segment_tail_node in neighbor.in_nodes:
                        edge_key = (segment_tail_node, neighbor)
                        edge = self.graphdb.edge_lookup_table[edge_key]
                        
                        edge.in_node = new_intersection
                        print("adding key " + str((new_intersection.id, neighbor.id)) + ": " + str((new_intersection, neighbor)) + " = " + str(edge))
                        self.graphdb.edge_lookup_table[(new_intersection, neighbor)] = edge
                        try:
                            del self.graphdb.edge_lookup_table[edge_key]
                        except:
                            print(f'Edge key {edge_key} does not exists already!')
                        
                        neighbor.in_nodes.remove(segment_tail_node)
                        neighbor.in_nodes.append(new_intersection)
                        
                        edge.old_key = edge_key
                        touched_edges.append(edge)

                print("segment: " + str(segment.id))
                print("touched edges: " + str(len(touched_edges)))
                print("set touched edges: " + str(len(set(touched_edges))))
                
                if len(touched_edges) == 0:
                    try:
                        del self.graphdb.nodes[node_id - 1]
                    except:
                        print(f'Node {node_id - 1} does not exists already!')
                    node_id -= 1
                    closed_segments_list.append(segment)
                    continue
                
                touched_segments = [edge.segment for edge in set(touched_edges)]

                bag_of_edges = set()
                
                for touched_segment in touched_segments:
                    bag_of_edges.update(touched_segment.edges)
                
                print("bag of edges: " + str(len(bag_of_edges)))
                
                segment_obs = [all_segment_obs[segment.id] for segment in touched_segments]

                all_traces_pass = True
                
                for traces in segment_obs:
                    
                    for trace in traces:
                        
                        trace_error = 0.0
                        
                        for obs in trace:
                            _, obs_lat, obs_lon, obs_time = obs
                            
                            obs_lat = float(obs_lat)
                            obs_lon = float(obs_lon)
                            
                            min_dist = float('infinity')
                            
                            for edge in bag_of_edges:
                                _, _, projected_dist = spatialfunclib.projection_onto_line(edge.in_node.latitude, edge.in_node.longitude, edge.out_node.latitude, edge.out_node.longitude, obs_lat, obs_lon)
                                
                                if projected_dist < min_dist:
                                    min_dist = projected_dist
                            
                            trace_error += min_dist ** 2
                        
                        trace_rmse = math.sqrt(float(trace_error) / float(len(trace)))
                        
                        if trace_rmse > 12.0:
                            print("trace rmse: " + str(trace_rmse))
                            all_traces_pass = False
                            break
                    
                    if all_traces_pass is False:
                        break
                
                if all_traces_pass is True:

                    reciprocal_segment_key = (segment.tail_edge.out_node, segment.head_edge.in_node)
                    
                    if reciprocal_segment_key in self.graphdb.segment_lookup_table:
                        reciprocal_segment = self.graphdb.segment_lookup_table[reciprocal_segment_key]
                        
                        if (reciprocal_segment != segment) and (reciprocal_segment.id in self.graphdb.segments):
                            try:
                                del self.graphdb.segments[reciprocal_segment.id]
                            except:
                                print(f'Segments {reciprocal_segment.id} does not exists already!')

                    try:
                        del self.graphdb.segments[segment.id]
                    except:
                        print(f'Segments {segment.id} does not exists already!')
                
                else:
                    print("at least one trace failed! boo! :-(\n")
                    for edge in touched_edges:
                        print("delete " + str((edge.in_node.id, edge.out_node.id)) + ": " + str((edge.in_node, edge.out_node)) + " = " + str(edge))

                        try:
                            del self.graphdb.edge_lookup_table[(edge.in_node, edge.out_node)]
                        except:
                            print(f'Edge key {(edge.in_node, edge.out_node)} does not exists already!')
                        self.graphdb.edge_lookup_table[edge.old_key] = edge
                        
                        if edge.old_key[0] == edge.in_node:
                            edge.in_node.out_nodes.remove(edge.out_node)
                            edge.in_node.out_nodes.append(edge.old_key[1])
                            edge.out_node = edge.old_key[1]
                        else:
                            edge.out_node.in_nodes.remove(edge.in_node)
                            edge.out_node.in_nodes.append(edge.old_key[0])
                            edge.in_node = edge.old_key[0]
                        
                    try:
                        del self.graphdb.nodes[node_id - 1]
                    except:
                        print(f'Node {node_id - 1} does not exists already!')
                    node_id -= 1
                
                closed_segments_list.append(segment)
                print("")

        print("done.\n")
        print("Saving new map... ")
        
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

            for edge in segment.edges:
                cur.execute("INSERT INTO edges VALUES (" + str(edge.id) + "," + str(edge.in_node.id) + "," + str(edge.out_node.id) + "," + str(segment_weight) + ")")
                
                valid_nodes.add(edge.in_node)
                valid_nodes.add(edge.out_node)
        
        for node in valid_nodes:
            cur.execute("INSERT INTO nodes VALUES (" + str(node.id) + "," + str(node.latitude) + "," + str(node.longitude) + "," + str(node.weight) + ")")
            
            if (node.id in self.graphdb.intersections):
                cur.execute("INSERT INTO intersections VALUES (" + str(node.id) + ")")
        
        conn.commit()
        conn.close()
        print("done.\n")


import os
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edge pruning on map graph')
    parser.add_argument('--input_graph_file', type=str, help='Path to graph sqlite database file')
    parser.add_argument('--match_trajs_path', type=str, help='Directory to matched trajectories txt file')
    parser.add_argument('--processed_map_path', type=str, help='Path to save processed map')
    args = parser.parse_args()

    graphdb_filename = args.input_graph_file
    matched_traces_filename = args.match_trajs_path
    output_filename = args.processed_map_path
    
    print("graphdb filename: " + str(graphdb_filename))
    print("matched traces filename: " + str(matched_traces_filename))
    print("output filename: " + str(output_filename))
    
    r = RefineTopology(graphdb_filename)
    r.process(matched_traces_filename, output_filename)
