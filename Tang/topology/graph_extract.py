#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.ndimage import imread
# from scipy.misc import imsave
from itertools import izip
from collections import deque
# from pylibs.spatialfunclib import projection_onto_line
# import sqlite3
# import math
# import sys
# import os

# globals
min_lat, min_lon, max_lat, max_lon = None, None, None, None
height = None
width = None
xscale = None
yscale = None


def projection_onto_line(a_lat, a_lon, b_lat, b_lon, c_lat, c_lon):
    dx1 = b_lat - a_lat
    dy1 = b_lon - a_lon
    dx2 = c_lat - a_lat
    dy2 = c_lon - a_lon
    return np.abs(dx1*dy2-dy1*dx2) / np.sqrt(dx1*dx1+dy1*dy1)


def douglas_peucker(segment, epsilon):
    dmax = 0
    index = 0

    for i in range(1, len(segment) - 1):
        # (_, _, d) = projection_onto_line(segment[0].latitude, segment[0].longitude, segment[-1].latitude, segment[-1].longitude, segment[i].latitude, segment[i].longitude)
        d = projection_onto_line(segment[0].latitude, segment[0].longitude, segment[-1].latitude, segment[-1].longitude, segment[i].latitude, segment[i].longitude)

        if (d > dmax):
            index = i
            dmax = d

    if (dmax >= epsilon):
        rec_results1 = douglas_peucker(segment[0:index], epsilon)
        rec_results2 = douglas_peucker(segment[index:], epsilon)

        smoothed_segment = rec_results1
        smoothed_segment.extend(rec_results2)
    else:
        smoothed_segment = [segment[0], segment[-1]]

    return smoothed_segment

def pixels_to_coords((i, j)):
    # return ((((height - i) / yscale) + min_lat), ((j / xscale) + min_lon))
    return (((j / xscale) + min_lat), (((height - i) / yscale) + min_lon))

class Node:
    def __init__(self, (latitude, longitude), weight):
        self.id = None
        self.latitude = latitude
        self.longitude = longitude
        self.weight = weight

class MainCrossing:
    def __init__(self, crossing_stack):
        self.component_crossings = []
        self.i = 0
        self.j = 0

        for crossing in crossing_stack:
            self.component_crossings.append(crossing)
            self.i += crossing[0]
            self.j += crossing[1]

        self.i /= float(len(crossing_stack))
        self.j /= float(len(crossing_stack))

    @property
    def location(self):
        return (self.i, self.j)

class Graph:
    def __init__(self):
        pass


    def extract(self, skeleton, density_estimate):
        skeleton = self.identify_crossing_points(skeleton)
        main_crossings, segments = self.find_main_crossings_and_segments(skeleton)

        self.create_graph(main_crossings, segments, density_estimate)


    def create_graph(self, main_crossings, segments, density_estimate):
        nodes, new_segments, intersections = self.create_nodes_and_new_segments(main_crossings, segments, density_estimate)

        node_id = 0
        edge_id = 0
        segment_id = 0

        fnode = open('vertices.txt', 'w')
        fedge = open('edges.txt', 'w')
        for segment in new_segments:
            # segment_weight = 0
            #
            # if (len(segment) > 2):
            #     for i in range(1, len(segment) - 1):
            #         segment_weight += segment[i].weight
            #     segment_weight /= float(len(segment) - 2)
            # else:
            #     segment_weight = float(segment[0].weight + segment[1].weight) / 2.0

            # remove unnecessary intermediate points with Douglas-Peucker
            smoothed_segment = douglas_peucker(segment, 10)


            for node in smoothed_segment:
                if (node.id is None):
                    node.id = node_id
                    # cur.execute("INSERT INTO nodes VALUES (" + str(node.id) + "," + str(node.latitude) + "," + str(node.longitude) + "," + str(node.weight) + ")")
                    fnode.write("{} {} {}\n".format(node.id, node.latitude, node.longitude))
                    node_id += 1


            outbound_segment_edge_ids = []
            for i in range(0, len(smoothed_segment) - 1):
                # cur.execute("INSERT INTO edges VALUES (" + str(edge_id) + "," + str(smoothed_segment[i].id) + "," + str(smoothed_segment[i + 1].id) + "," + str(segment_weight) + ")")
                fedge.write("{} {} {}\n".format(edge_id, smoothed_segment[i].id, smoothed_segment[i + 1].id))
                outbound_segment_edge_ids.append(edge_id)
                edge_id += 1


        fnode.close()
        fedge.close()


    def create_nodes_and_new_segments(self, main_crossings, segments, density_estimate):
        # density_map = [2**x for x in range(16, 3, -1)] + range(15, 0, -1)
        # density_map.reverse()

        nodes = {}
        new_segments = []
        intersections = set()

        for segment in segments:
            new_segment = []

            head_node = main_crossings[segment[0]].location

            if (head_node not in nodes):
                nodes[head_node] = Node(pixels_to_coords(head_node), 1)

            new_segment = [nodes[head_node]]
            intersections.add(nodes[head_node])

            for i in range(1, len(segment) - 1):
                if (segment[i] not in nodes):
                    nodes[segment[i]] = Node(pixels_to_coords(segment[i]), 1)

                new_segment.append(nodes[segment[i]])

            tail_node = main_crossings[segment[-1]].location

            if (tail_node not in nodes):
                nodes[tail_node] = Node(pixels_to_coords(tail_node), 1)

            new_segment.append(nodes[tail_node])
            intersections.add(nodes[tail_node])

            new_segments.append(new_segment)

        return nodes, new_segments, intersections

    def find_main_crossings_and_segments(self, skeleton):
        crossing_pixels = np.where(skeleton == 2)
        print "crossing_pixels: " + str(len(crossing_pixels[0]))

        curr_count = 1
        total_count = len(crossing_pixels[0])

        main_crossings = {}
        segments = []

        for (i, j) in izip(crossing_pixels[0], crossing_pixels[1]):
            if ((curr_count % 100 == 0) or (curr_count == total_count)):
                sys.stdout.write("\n" + str(curr_count) + "/" + str(total_count) + "... ")
                sys.stdout.flush()
            curr_count += 1

            #
            # begin extended combustion (to consume adjacent intersection pixels)
            #
            crossing_stack = []
            combusting_queue = deque([])

            if (skeleton[i][j] == 2):
                skeleton[i][j] = 3
                combusting_queue.appendleft((i, j))
            else:
                if ((i, j) not in main_crossings):
                    print "ERROR!! (" + str(i) + "," + str(j) + ") not in main_crossings!"
                    exit()

            while (len(combusting_queue) > 0):
                current_crossing = combusting_queue.pop()
                crossing_stack.append(current_crossing)

                (m, n) = current_crossing

                # north
                if (skeleton[m - 1][n] == 2):
                    skeleton[m - 1][n] = 3
                    combusting_queue.appendleft((m - 1, n))

                # north-east
                if (skeleton[m - 1][n + 1] == 2):
                    skeleton[m - 1][n + 1] = 3
                    combusting_queue.appendleft((m - 1, n + 1))

                # east
                if (skeleton[m][n + 1] == 2):
                    skeleton[m][n + 1] = 3
                    combusting_queue.appendleft((m, n + 1))

                # south-east
                if (skeleton[m + 1][n + 1] == 2):
                    skeleton[m + 1][n + 1] = 3
                    combusting_queue.appendleft((m + 1, n + 1))

                # south
                if (skeleton[m + 1][n] == 2):
                    skeleton[m + 1][n] = 3
                    combusting_queue.appendleft((m + 1, n))

                # south-west
                if (skeleton[m + 1][n - 1] == 2):
                    skeleton[m + 1][n - 1] = 3
                    combusting_queue.appendleft((m + 1, n - 1))

                # west
                if (skeleton[m][n - 1] == 2):
                    skeleton[m][n - 1] = 3
                    combusting_queue.appendleft((m, n - 1))

                # north-west
                if (skeleton[m - 1][n - 1] == 2):
                    skeleton[m - 1][n - 1] = 3
                    combusting_queue.appendleft((m - 1, n - 1))

            if (len(crossing_stack) > 0):
                new_main_crossing = MainCrossing(crossing_stack)

                for crossing in crossing_stack:
                    main_crossings[crossing] = new_main_crossing

            #
            # end extended combustion (all adjacent intersection pixels consumed)
            #

            # mark current crossing point as "do not return"
            skeleton[i][j] = -1

            # north
            if (skeleton[i - 1][j] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i - 1, j), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # north-east
            if (skeleton[i - 1][j + 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i - 1, j + 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # east
            if (skeleton[i][j + 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i, j + 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # south-east
            if (skeleton[i + 1][j + 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i + 1, j + 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # south
            if (skeleton[i + 1][j] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i + 1, j), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # south-west
            if (skeleton[i + 1][j - 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i + 1, j - 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # west
            if (skeleton[i][j - 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i, j - 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # north-west
            if (skeleton[i - 1][j - 1] == 1):
                edge_nodes, skeleton = self.find_edge_nodes((i - 1, j - 1), skeleton, [(i, j)])
                segments.append(edge_nodes)

            # reset crossing point value
            skeleton[i][j] = 3

        print "done."

        #imsave("no_edges_skeleton.png", skeleton)
        return main_crossings, segments

    def find_edge_nodes(self, start_location, skeleton, edge_nodes):
        queue = deque([])
        queue.appendleft(start_location)

        (i, j) = start_location
        skeleton[i][j] = 0

        while (len(queue) > 0):
            curr_location = queue.pop()
            edge_nodes.append(curr_location)

            (i, j) = curr_location

            # north
            if (skeleton[i - 1][j] == 1):
                skeleton[i - 1][j] = 0
                queue.appendleft((i - 1, j))

            # east
            if (skeleton[i][j + 1] == 1):
                skeleton[i][j + 1] = 0
                queue.appendleft((i, j + 1))

            # south
            if (skeleton[i + 1][j] == 1):
                skeleton[i + 1][j] = 0
                queue.appendleft((i + 1, j))

            # west
            if (skeleton[i][j - 1] == 1):
                skeleton[i][j - 1] = 0
                queue.appendleft((i, j - 1))

            # north-east
            if (skeleton[i - 1][j + 1] == 1):
                skeleton[i - 1][j + 1] = 0
                queue.appendleft((i - 1, j + 1))

            # south-east
            if (skeleton[i + 1][j + 1] == 1):
                skeleton[i + 1][j + 1] = 0
                queue.appendleft((i + 1, j + 1))

            # south-west
            if (skeleton[i + 1][j - 1] == 1):
                skeleton[i + 1][j - 1] = 0
                queue.appendleft((i + 1, j - 1))

            # north-west
            if (skeleton[i - 1][j - 1] == 1):
                skeleton[i - 1][j - 1] = 0
                queue.appendleft((i - 1, j - 1))

        # find intersection at end of segment
        for k in range(-1, (-1 * len(edge_nodes)), -1):
            (i, j) = edge_nodes[k]

            # north
            if (skeleton[i - 1][j] >= 2):
                edge_nodes.append((i - 1, j))

            # east
            elif (skeleton[i][j + 1] >= 2):
                edge_nodes.append((i, j + 1))

            # south
            elif (skeleton[i + 1][j] >= 2):
                edge_nodes.append((i + 1, j))

            # west
            elif (skeleton[i][j - 1] >= 2):
                edge_nodes.append((i, j - 1))

            # north-east
            elif (skeleton[i - 1][j + 1] >= 2):
                edge_nodes.append((i - 1, j + 1))

            # south-east
            elif (skeleton[i + 1][j + 1] >= 2):
                edge_nodes.append((i + 1, j + 1))

            # south-west
            elif (skeleton[i + 1][j - 1] >= 2):
                edge_nodes.append((i + 1, j - 1))

            # north-west
            elif (skeleton[i - 1][j - 1] >= 2):
                edge_nodes.append((i - 1, j - 1))

        # sanity check -- segment is bookended by two different intersections
        (i, j) = edge_nodes[-1]
        if (skeleton[i][j] < 2):
            print "\nERROR!! No intersection at segment end!"
            exit()

        return edge_nodes, skeleton

    def identify_crossing_points(self, skeleton):
        fg_pixels = np.where(skeleton == 1)
        print "fg_pixels: " + str(len(fg_pixels[0]))

        curr_count = 1
        total_count = len(fg_pixels[0])

        crossing_skeleton = np.copy(skeleton)

        for (i, j) in izip(fg_pixels[0], fg_pixels[1]):
            if ((curr_count % 100 == 0) or (curr_count == total_count)):
                sys.stdout.write("\n" + str(curr_count) + "/" + str(total_count) + "... ")
                sys.stdout.flush()
            curr_count += 1

            p = [skeleton[i - 1][j], skeleton[i - 1][j + 1], skeleton[i][j + 1], skeleton[i + 1][j + 1], skeleton[i + 1][j], skeleton[i + 1][j - 1], skeleton[i][j - 1], skeleton[i - 1][j - 1], skeleton[i - 2][j], skeleton[i - 2][j + 1], skeleton[i - 2][j + 2], skeleton[i - 1][j + 2], skeleton[i][j + 2], skeleton[i + 1][j + 2], skeleton[i + 2][j + 2], skeleton[i + 2][j + 1], skeleton[i + 2][j], skeleton[i + 2][j - 1], skeleton[i + 2][j - 2], skeleton[i + 1][j - 2], skeleton[i][j - 2], skeleton[i - 1][j - 2], skeleton[i - 2][j - 2], skeleton[i - 2][j - 1]]

            fringe = [bool(p[8] and bool(p[7] or p[0] or p[1])), bool(p[9] and bool(p[0] or p[1])), bool(p[10] and p[1]), bool(p[11] and bool(p[1] or p[2])), bool(p[12] and bool(p[1] or p[2] or p[3])), bool(p[13] and bool(p[2] or p[3])), bool(p[14] and p[3]), bool(p[15] and bool(p[3] or p[4])), bool(p[16] and bool(p[3] or p[4] or p[5])), bool(p[17] and bool(p[4] or p[5])), bool(p[18] and p[5]), bool(p[19] and bool(p[5] or p[6])), bool(p[20] and bool(p[5] or p[6] or p[7])), bool(p[21] and bool(p[6] or p[7])), bool(p[22] and p[7]), bool(p[23] and bool(p[7] or p[0]))]

            connected_component_count = 0
            for k in range(0, len(fringe)):
                connected_component_count += int(not bool(fringe[k]) and bool(fringe[(k + 1) % len(fringe)]))

            if (connected_component_count == 0):
                crossing_skeleton[i][j] = 0
            elif ((connected_component_count == 1) or (connected_component_count > 2)):
                crossing_skeleton[i][j] = 2

        print "done."

        #imsave("crossing_skeleton.png", crossing_skeleton)
        return crossing_skeleton


import sys, time


def main(skeleton_filename="skel.png",bounding_box_filename="boundingbox.txt"):
    print("skeleton filename: " + str(skeleton_filename))
    print("bounding box filename: " + str(bounding_box_filename))

    skeleton = imread(skeleton_filename)

    # set up globals
    bounding_box_file = open(bounding_box_filename, 'r')
    bounding_box_values = bounding_box_file.readline().strip("\n").split(" ")
    bounding_box_file.close()

    global min_lat, min_lon, max_lat, max_lon, height, width, xscale, yscale
    min_lat, min_lon, max_lat, max_lon = float(bounding_box_values[0]), float(bounding_box_values[1]), float(
        bounding_box_values[2]), float(bounding_box_values[3])

    height = len(skeleton)
    width = len(skeleton[0])

    yscale = height / (max_lon - min_lon)
    xscale = width / (max_lat - min_lat)

    g = Graph()

    start_time = time.time()
    g.extract(skeleton.astype(np.bool).astype(np.int), skeleton)
    print("total elapsed time: " + str(time.time() - start_time) + " seconds")


if __name__ == '__main__':
    #
    # usage: python graph_extract.py skeletons/skeleton_7m.png bounding_boxes/bounding_box_7m.txt skeleton_maps/skeleton_map_7m.db
    #
    skeleton_filename = "skel.png"
    bounding_box_filename = "boundingbox.txt"

    main(skeleton_filename, bounding_box_filename)
