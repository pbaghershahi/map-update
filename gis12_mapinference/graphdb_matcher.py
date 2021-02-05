from streetmap import *
from gpsmatcher import GPSMatcher
from spatialfunclib import *
from mathfunclib import *
import time
import sys

#note: to compute emission probability between edges and map which is a representation of spatial probability in hmm models
EMISSION_SIGMA = 50.0  # 25.0
EMISSION_UNKNOWN = 0.01

TRANSITION_UNKNOWN = 0.00001
TRANSITION_UNKNOWN_UNKNOWN = 0.9
TRANSITION_SELF = 0.5
TRANSITION_UTURN = 0.00001

MAX_DIST_SUBDIVISION_HMM = 20.0


class GraphDBMatcher(GPSMatcher):
    def __init__(self, mapdb, constraint_length=300, MAX_DIST=100):

        # note: computes the HMM networks which consists of states and transition probability
        #  between each pair of them it is a dictionary with HMM states represented by edges
        #  as keys of type ((start_lat, start_lon), (end_lat, end_lon)) and transition probabilities as values
        hmm = self.mapdb_to_hmm(mapdb)

        # precompute probability table
        # note: to compute emission probability in viterbi algorithm for each state
        #  based on observation distance from edges of the map by the use of normal distribution
        emission_probabilities = [
            complementary_normal_distribution_cdf(x, 0, EMISSION_SIGMA) for x in range(0, int(3.0 * EMISSION_SIGMA))
        ]
        # print(emission_probabilities)

        # note: projects coord which is a node on an edge of the map and
        #  computes the distance between the main node and its projection
        def emission_probability(state, coord):
            if state == 'unknown':
                return EMISSION_UNKNOWN
            edge = state
            projected_point = project_onto_segment(edge, coord)
            distance = haversine_distance(projected_point, coord)
            # note: 3 in the below condition is because of normal distribution (over 3*sigma probability is near 0)
            if int(distance) >= 3 * EMISSION_SIGMA:
                return 0
            return emission_probabilities[int(distance)]

        # sys.stdout.write("Initing GPS matcher... ")
        # sys.stdout.flush()
        print("Initiating GPS matcher... ")
        GPSMatcher.__init__(self, hmm, emission_probability, constraint_length, MAX_DIST, priors={'unknown': 1.0})
        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")

    #
    # add nodes between original map nodes at 20m apart
    #
    def recursive_map_subdivide(self, themap, node):

        # counter is used to assign different values to multiple edges from a node while subdividing
        counter = 0

        # subdivide edges between this node and all of its outnodes
        node_outnodes = list(node.out_nodes)
        for nextnode in node_outnodes:
            dist = haversine_distance(node.coords(), nextnode.coords())

            if dist > MAX_DIST_SUBDIVISION_HMM:
                node_lat, node_lon = node.coords()
                nextnode_lat, nextnode_lon = nextnode.coords()
                # get new node MAX_DIST_SUBDIVISION_HMM apart from this node
                newlat, newlon = point_along_line(node_lat, node_lon, nextnode_lat, nextnode_lon,
                                                  MAX_DIST_SUBDIVISION_HMM / dist)

                # id = str(node.id)+"."+str(counter)
                newnode = Node(newlat, newlon)

                # make nextnode of this node as out_nodes of new node
                newnode.out_nodes = [nextnode]

                # remove this node's nextnode from out_nodes and put new node in the this node's out_nodes
                node.out_nodes.remove(nextnode)
                node.out_nodes.insert(0, newnode)

                # put new node in the map
                themap.nodes[newnode.id] = newnode

                # recursively subdivide for the newly created node
                self.recursive_map_subdivide(themap, newnode)
                counter += 1
            else:
                continue

    #
    # for all original map nodes call recursive_map_subdevide() to
    # to devide the map edges in 20m segements
    #
    def map_subdivide(self, themap):
        orig_map = themap
        for node in list(orig_map.nodes.values()):
            self.recursive_map_subdivide(themap, node)

    def mapdb_to_hmm(self, mapdb):
        themap = StreetMap()
        themap.load_graphdb(mapdb)
        # themap.load_osmdb(mapdb)

        # sys.stdout.write("Subdividing map... ")
        # sys.stdout.flush()
        print("Subdividing map... ")

        # subdivide the map in 20 m segemetns
        self.map_subdivide(themap)

        # sys.stdout.write("into " + str(len(themap.nodes)) + " nodes.\n")
        # sys.stdout.flush()
        print("into " + str(len(themap.nodes)) + " nodes.\n")

        # sys.stdout.write("Creating HMM... ")
        # sys.stdout.flush()
        print("Creating HMM... ")

        hmm = {}
        for from_edge in list(themap.edges.values()):
            from_edge_key = (from_edge.in_node.coords(), from_edge.out_node.coords())
            # print(('unknown', TRANSITION_UNKNOWN), (from_edge_key, TRANSITION_SELF))
            hmm[from_edge_key] = [('unknown', TRANSITION_UNKNOWN), (from_edge_key, TRANSITION_SELF)]

            # don't count our own (u-turned) weight in the sum - we almost never uturn anyway
            to_edges_sum_weight = sum([x.weight for x in from_edge.out_edges])  # - from_edge.weight

            for to_edge in from_edge.out_edges:
                to_edge_key = (to_edge.in_node.coords(), to_edge.out_node.coords())

                if to_edge.out_node != from_edge.in_node:
                    hmm[from_edge_key] += [(to_edge_key, (to_edge.weight / to_edges_sum_weight) * (1.0 - TRANSITION_SELF - TRANSITION_UNKNOWN))]
                # if this is a u-turn, only allow it if it's at an intersection, and even then make it very unlikely
                elif len(from_edge.out_edges) != 2:
                    hmm[from_edge_key] += [(to_edge_key, TRANSITION_UTURN)]

        hmm['unknown'] = [('unknown', TRANSITION_UNKNOWN_UNKNOWN)]
        hmm['unknown'] += [
            ((edge.in_node.coords(), edge.out_node.coords()), (1 - TRANSITION_UNKNOWN_UNKNOWN) / len(themap.edges)) for
            edge in list(themap.edges.values())]

        # sys.stdout.write("done.\n")
        # sys.stdout.flush()
        print("done.\n")

        return hmm
