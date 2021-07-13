import sqlite3
import pyximport; pyximport.install()
from pylibs import spatialfunclib
from pylibs import spatialfunclib_accel
from rtree import Rtree

intersection_size = 50.0 # meters


class Node:
    id_counter = 1

    def __init__(self, latitude, longitude, id=None, weight=0.0):
        if id is not None:
            Node.id_counter = max(Node.id_counter, id+1)
        else:
            id = Node.id_counter1000
            Node.id_counter += 1

        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.weight = weight
        self.in_nodes = []
        self.out_nodes = []
        self.intersection = None
        self.visited = False

    def coords(self):
        return (self.latitude,self.longitude)

    def distance_to(self, lat, lon):
#        return spatialfunclib.distance(self.latitude, self.longitude, lat, lon)
        return spatialfunclib_accel.fast_distance(self.latitude, self.longitude, lat, lon)

class Edge:
    id_counter = 1
    def __init__(self, in_node, out_node, id=None, weight=0.0, segment=None):
        if id is not None:
            Edge.id_counter = max(Edge.id_counter, id+1)
        else:
            id = Edge.id_counter
            Edge.id_counter += 1

        self.id = id
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.segment = segment
        self.in_edges = []
        self.out_edges = []
        self.visited = False

    @property
    def length(self):
        return spatialfunclib.distance(self.in_node.latitude, self.in_node.longitude, self.out_node.latitude, self.out_node.longitude)

    @property
    def bearing(self):
        return spatialfunclib.path_bearing(self.in_node.latitude, self.in_node.longitude, self.out_node.latitude, self.out_node.longitude)

    def point_at_meters_along(self, meters):
        return spatialfunclib.point_along_line(
            self.in_node.latitude,
            self.in_node.longitude,
            self.out_node.latitude,
            self.out_node.longitude,
            meters / self.length
        )


class Segment:
    id_counter = 1

    def __init__(self, id=None, edges=[]):
        if id is not None:
            Segment.id_counter = max(Segment.id_counter, id+1)
        else:
            id = Segment.id_counter
            Segment.id_counter += 1

        self.id = id
        self.edges = edges

    # note: head edge is the first edge of the trip
    @property
    def head_edge(self):
        return self.edges[0]

    @property
    def length(self):
        sum = 0.0
        for edge in self.edges:
            sum += edge.length
        return sum

    # note: tail edge is the first edge of the trip
    @property
    def tail_edge(self):
        return self.edges[-1]

    # if you get Nones in this list, that's because you didn't set the segment in the Edge
    def out_segments(self):
        return [x.segment for x in self.edges[-1].out_edges]

    # if you get Nones in this list, that's because you didn't set the segment in the Edge
    def in_segments(self):
        return [x.segment for x in self.edges[0].in_edges]


class Intersection:
    def __init__(self, id, nodes):
        self.id = id
        self.nodes = nodes
        (self.latitude, self.longitude) = self._find_mean_location(nodes)

    def _find_mean_location(self, nodes):

        # initialize location
        latitude = 0.0
        longitude = 0.0

        for node in self.nodes:

            latitude += node.latitude
            longitude += node.longitude

            # set node's intersection attribute value
            node.intersection = self

        # average latitude and longitude values
        latitude = (latitude / len(self.nodes))
        longitude = (longitude / len(self.nodes))

        return latitude, longitude

class StreetMap:
    def __init__(self):
        self.nodes = {} # indexed by node id
        self.edges = {} # indexed by edge id
        self.intersections = {} # indexed by node id
        self.node_spatial_index = Rtree()
        self.edge_spatial_index = Rtree()
        self.intersection_spatial_index = Rtree()
        self.edge_lookup_table = {} # indexed by (in_node,out_node)
        self.edge_coords_lookup_table = {} # indexed by (in_node.coords, out_node.coords)
        self.segments = {} # indexed by segment id
        self.segment_lookup_table = {} # indexed by (head_edge.in_node, tail_edge.out_node)

    def load_graphdb(self, grapdb_filename):
        print(grapdb_filename)
        conn = sqlite3.connect(grapdb_filename)
        cur = conn.cursor()

        print("\nLoading nodes... ")

        cur.execute("select id, latitude, longitude, weight from nodes")
        query_result = cur.fetchall()

        for id, latitude, longitude, weight in query_result:

            self.nodes[id] = Node(latitude, longitude, id, weight)

        print("done.")
        print("Loading edges... ")


        cur.execute("select id, in_node, out_node, weight from edges")
        query_result = cur.fetchall()
        valid_edge_nodes = {} # indexed by node id

        for id, in_node_id, out_node_id, weight in query_result:

            in_node = self.nodes[in_node_id]
            out_node = self.nodes[out_node_id]

            if True:

                self.edges[id] = Edge(in_node, out_node, id, weight)

                if in_node not in out_node.in_nodes:
                    out_node.in_nodes.append(in_node)

                if out_node not in in_node.out_nodes:
                    in_node.out_nodes.append(out_node)

                if in_node.id not in list(valid_edge_nodes.keys()):
                    valid_edge_nodes[in_node.id] = in_node

                if out_node.id not in list(valid_edge_nodes.keys()):
                    valid_edge_nodes[out_node.id] = out_node

        cur.execute("select id, edge_ids from segments")
        query_result = cur.fetchall()

        for id, edge_ids in query_result:
            segment_edges = [self.edges[edge_id] for edge_id in eval(edge_ids)]
            self.segments[id] = Segment(id, segment_edges)

            self.segment_lookup_table[(self.segments[id].head_edge.in_node, self.segments[id].tail_edge.out_node)] = self.segments[id]

            for segment_edge in segment_edges:
                segment_edge.segment = self.segments[id]

        cur.execute("select node_id from intersections")
        query_result = cur.fetchall()

        for node_id in query_result:
            self.intersections[node_id[0]] = self.nodes[node_id[0]]


        try:
            cur.execute("select transition_segment, from_segment, to_segment from transitions");
            query_result = cur.fetchall()
            self.transitions = {}
            for transition_segment, from_segment, to_segment in query_result:
                self.transitions[transition_segment]=(from_segment,to_segment)
        except:
            print("Got an error reading ")

        print("done.")

        conn.close()

        self.nodes = valid_edge_nodes
        self._index_nodes()
        self._index_edges()

        print("Map has " + str(len(self.nodes)) + " nodes, " + str(len(self.edges)) + " edges, " + str(len(self.segments)) + " segments and " + str(len(self.intersections)) + " intersections.")

    def _index_nodes(self):

        print("Indexing nodes... ")

        for curr_node in list(self.nodes.values()):
            self.node_spatial_index.insert(curr_node.id, (curr_node.longitude, curr_node.latitude))

        print("done.")

    def _index_edges(self):

        print("Indexing edges... ")

        for curr_edge in list(self.edges.values()):
            curr_edge_minx = min(curr_edge.in_node.longitude, curr_edge.out_node.longitude)
            curr_edge_miny = min(curr_edge.in_node.latitude, curr_edge.out_node.latitude)
            curr_edge_maxx = max(curr_edge.in_node.longitude, curr_edge.out_node.longitude)
            curr_edge_maxy = max(curr_edge.in_node.latitude, curr_edge.out_node.latitude)
            self.edge_spatial_index.insert(curr_edge.id, (curr_edge_minx, curr_edge_miny, curr_edge_maxx, curr_edge_maxy))
            self.edge_lookup_table[(curr_edge.in_node, curr_edge.out_node)] = curr_edge
            self.edge_coords_lookup_table[(curr_edge.in_node.coords(), curr_edge.out_node.coords())] = curr_edge

        for edge in list(self.edges.values()):
            for out_node_neighbor in edge.out_node.out_nodes:
                edge.out_edges.append(self.edge_lookup_table[(edge.out_node, out_node_neighbor)])

            for in_node_neighbor in edge.in_node.in_nodes:
                edge.in_edges.append(self.edge_lookup_table[(in_node_neighbor, edge.in_node)])

        print("done.")

    def _find_and_index_intersections(self):

        # output that we are finding and indexing intersections
        sys.stdout.write("Finding and indexing intersections... ")
        sys.stdout.flush()

        # find intersection nodes and index
        (intersection_nodes, intersection_nodes_index) = self._find_intersection_nodes()

        # storage for intersection nodes already placed in intersections
        placed_intersection_nodes = set()

        # define longitude/latitude offset for bounding box
        lon_offset = ((intersection_size / 2.0) / spatialfunclib.METERS_PER_DEGREE_LONGITUDE)
        lat_offset = ((intersection_size / 2.0) / spatialfunclib.METERS_PER_DEGREE_LATITUDE)

        intersection_id = 0

        for intersection_node in intersection_nodes:
            if intersection_node not in placed_intersection_nodes:
                bounding_box = (intersection_node.longitude - lon_offset, intersection_node.latitude - lat_offset, intersection_node.longitude + lon_offset, intersection_node.latitude + lat_offset)

                # find intersection node ids within bounding box
                intersection_node_ids = intersection_nodes_index.intersection(bounding_box)
                intersection_nodes = list(map(self._get_node, intersection_node_ids))
                placed_intersection_nodes.update(intersection_nodes)
                new_intersection = Intersection(intersection_id, intersection_nodes)
                intersection_id += 1
                self.intersections[new_intersection.id] = new_intersection
                self.intersection_spatial_index.insert(new_intersection.id, (new_intersection.longitude, new_intersection.latitude))

        print("done.")

    def _get_node(self, node_id):
        return self.nodes[node_id]

    def _find_intersection_nodes(self):
        intersection_nodes = []
        intersection_nodes_index = Rtree()

        for curr_node in list(self.nodes.values()):
            neighbors = set()
            for in_node in curr_node.in_nodes:
                neighbors.add(in_node)

            for out_node in curr_node.out_nodes:
                neighbors.add(out_node)

            if len(neighbors) > 2:
                intersection_nodes.append(curr_node)
                intersection_nodes_index.insert(curr_node.id, (curr_node.longitude, curr_node.latitude))

        return intersection_nodes, intersection_nodes_index

    def _valid_node(self, node):

        # if node falls inside the designated bounding box
        if (node.latitude >= 41.8619 and node.latitude <= 41.8842) and (node.longitude >= -87.6874 and node.longitude <= -87.6398):

            return True
        else:
            return False

    def _valid_highway_edge(self, highway_tag_value):
        if ((highway_tag_value == 'primary') or
                (highway_tag_value == 'secondary') or
                (highway_tag_value == 'tertiary') or
                (highway_tag_value == 'residential')):

            return True
        else:
            return False

    def reset_node_visited_flags(self):
        for node in list(self.nodes.values()):
            node.visited = False

    def reset_edge_visited_flags(self):
        for edge in list(self.edges.values()):
            edge.visited = False

    def write_map_to_file(self, map_filename="map.txt"):
        print("\nWriting map to file... ")

        with open(map_filename, 'w') as map_file:
            for curr_edge in list(self.edges.values()):
                map_file.write(str(curr_edge.in_node.latitude) + "," + str(curr_edge.in_node.longitude) + "\n")
                map_file.write(str(curr_edge.out_node.latitude) + "," + str(curr_edge.out_node.longitude) + "\n\n")

        print("done.")

    def _distance(self, location1, location2):
        return spatialfunclib.distance(location1.latitude, location1.longitude, location2.latitude, location2.longitude)

import sys
import time
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edge pruning on map graph')
    parser.add_argument('--file_type', type=str, default='graphdb', help='type of the input graph file')
    parser.add_argument('--input_graph_file', type=str, help='Path to graph sqlite database file')
    parser.add_argument('--output_map_file', type=str, help='Path to save output map of edges in text format')
    args = parser.parse_args()

    start_time = time.time()
    db_type = args.file_type
    db_filename = args.input_graph_file
    output_filename = args.output_map_file

    m = StreetMap()
    m.load_graphdb(db_filename)
    m.write_map_to_file(str(output_filename))

    print("\nMap operations complete (in " + str(time.time() - start_time) + " seconds).\n")
