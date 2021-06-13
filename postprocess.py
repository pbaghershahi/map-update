import pandas as pd
import sqlite3
import geopandas as gp
from rtree import index
import numpy as np
from haversine import haversine, Unit

MAX_DIST = 20
MIN_LENGTH = 20
MAX_ANGLE = 10
METERS_PER_DEGREE_LATITUDE = 111070.34306591158
METERS_PER_DEGREE_LONGITUDE = 83044.98918812413


class GeoPoint:
    def __init__(self, geo_tuple):
        self.longitude = geo_tuple[0]
        self.latitude = geo_tuple[1]


def get_nearby(node, rtree_idx):
    nearby_edges = rtree_idx.intersection(
        (
            node.longitude - MAX_DIST / METERS_PER_DEGREE_LONGITUDE,
            node.latitude - MAX_DIST / METERS_PER_DEGREE_LATITUDE,
            node.longitude + MAX_DIST / METERS_PER_DEGREE_LONGITUDE,
            node.latitude + MAX_DIST / METERS_PER_DEGREE_LATITUDE
        )
    )
    return list(nearby_edges)


def ccw(A, B, C):
    return (C.latitude - A.latitude) * (B.longitude - A.longitude) > (B.latitude - A.latitude) * (
                C.longitude - A.longitude)


def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def nodes2vect(A, B):
    return np.array([B.longitude - A.longitude, B.latitude - A.latitude])


def nodes2normal(A, B):
    vect = nodes2vect(A, B)
    return np.array([vect[1], -vect[0]])


def project_vector(v, w):
    return v.dot(w) / v.dot(v) * v


def project_point(A, B, C):
    v = nodes2vect(A, B)
    w = nodes2vect(A, C)
    return np.array(A.longitude, A.latitude) + project_vector(v, w)


def angle(v, w):
    return np.degrees(np.arccos(v.dot(w) / (np.sqrt(v.dot(v)) * np.sqrt(w.dot(w)))))


def point_in(A, B, C):
    lay_in = (min(A.longitude, B.longitude) < C.longitude < max(A.longitude, B.longitude)) and \
             (min(A.latitude, B.latitude) < C.latitude < max(A.latitude, B.latitude))
    return lay_in


def dist_measure(x, y):
    return haversine(x[:2][::-1], y[:2][::-1], unit=Unit.METERS)


def line(A, B):
    dy = A.latitude - B.latitude
    dx = B.longitude - A.longitude
    return dy, dx, -(A.longitude * B.latitude - B.longitude * A.latitude)


def intersection(L1, L2):
    D = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return x, y
    else:
        return False


def dist_intersect(A, B, C, D):
    l1 = line(A, B)
    l2 = line(C, D)
    intr_point = intersection(l1, l2)
    min_dist = MAX_DIST
    if not intr_point:
        print('There is no intersection!')
        return None, None, min_dist
    nearest_point = None
    lay_in = (min(C.longitude, D.longitude) < intr_point[0] < max(C.longitude, D.longitude)) and \
             (min(C.latitude, D.latitude) < intr_point[1] < max(C.latitude, D.latitude))
    if lay_in:
        for node_idx, node in enumerate([A, B]):
            diff_dist = haversine((node.latitude, node.longitude), intr_point[::-1], unit=Unit.METERS)
            if diff_dist < min_dist:
                nearest_point = node
                min_dist = diff_dist
    return intr_point, nearest_point, min_dist


def postprocess(map_dbpath, method='generate_nodes'):
    conn = sqlite3.connect(map_dbpath)
    cur = conn.cursor()
    edges_df = pd.read_sql_query("SELECT id, in_node, out_node, weight FROM edges", conn)
    nodes_df = pd.read_sql_query("SELECT id, latitude, longitude, weight FROM nodes", conn)
    nodes_df.set_index('id', drop=True, inplace=True)
    edges_df['in_out'] = edges_df[['in_node', 'out_node']].apply(
        lambda x: tuple(y for y in x), axis=1
    )
    unique_indices = []
    for _, row in edges_df.iterrows():
        if row.in_out[::-1] not in unique_indices:
            unique_indices.append(row.in_out)
    omitted_indices = list(edges_df[~edges_df.in_out.isin(unique_indices)]['id'].values)
    edges_df = edges_df[edges_df.in_out.isin(unique_indices)]
    edges_df['way_length'] = edges_df.apply(
        lambda row: haversine(
            (nodes_df.loc[row.in_node].latitude, nodes_df.loc[row.in_node].longitude),
            (nodes_df.loc[row.out_node].latitude, nodes_df.loc[row.out_node].longitude),
            unit=Unit.METERS
            ),
        axis=1)
    omitted_indices += list(edges_df[edges_df.way_length <= MIN_LENGTH].id.values)
    edges_df = edges_df[edges_df.way_length > MIN_LENGTH]
    edges_df.reset_index(drop=True, inplace=True)

    for om_idx in omitted_indices:
        cur.execute(f"DELETE FROM edges WHERE id={om_idx};")
    idx = index.Index()
    for row_id, row in edges_df.iterrows():
        in_node = GeoPoint(list(nodes_df.loc[row.in_node][['longitude', 'latitude']]))
        out_node = GeoPoint(list(nodes_df.loc[row.out_node][['longitude', 'latitude']]))
        idx.insert(
            row_id,
            (
                min(in_node.longitude, out_node.longitude),
                min(in_node.latitude, out_node.latitude),
                max(in_node.longitude, out_node.longitude),
                max(in_node.latitude, out_node.latitude)
            )
        )

    weight = 1.0
    last_node_id = nodes_df.shape[0]
    for _, row in edges_df.iterrows():
        no_intersects = True
        in_node = GeoPoint(list(nodes_df.loc[row.in_node][['longitude', 'latitude']]))
        out_node = GeoPoint(list(nodes_df.loc[row.out_node][['longitude', 'latitude']]))
        nearby_edges = set(get_nearby(in_node, idx)).union(set(get_nearby(out_node, idx)))-{row.id}
        new_in_node = None
        new_out_node = None
        min_in_dist = MAX_DIST
        min_out_dist = MAX_DIST
        for edge_id in nearby_edges:
            temp_in = GeoPoint(list(nodes_df.loc[edges_df.loc[edge_id].in_node][['longitude', 'latitude']]))
            temp_out = GeoPoint(list(nodes_df.loc[edges_df.loc[edge_id].out_node][['longitude', 'latitude']]))
            if intersect(in_node, out_node, temp_in, temp_out):
                no_intersects = False
                break
            intr_point, nearest_node, min_dist = dist_intersect(
                in_node, out_node, temp_in, temp_out
            )
            if nearest_node == in_node:
                if min_dist < min_in_dist:
                    new_in_node = intr_point
                    min_in_dist = min_dist
            elif nearest_node == out_node:
                if min_dist < min_out_dist:
                    new_out_node = intr_point
                    min_out_dist = min_dist
        if new_in_node and no_intersects:
            nodes_df.loc[row.in_node]['longitude'], nodes_df.loc[row.in_node]['latitude'] = new_in_node[0], new_in_node[1]
            if method == 'generate_nodes':
                cur.execute(f"INSERT INTO nodes VALUES ({last_node_id},{new_in_node[1]},{new_in_node[0]},{weight});")
                cur.execute(f"UPDATE edges SET in_node={last_node_id} WHERE id={row.id};")
                last_node_id += 1
            elif method == 'replace_nodes':
                cur.execute(f"UPDATE nodes SET latitude={new_in_node[1]}, longitude={new_in_node[0]} WHERE id={row.in_node};")
            print(f'in node of edge id: {row.id} changes')
        if new_out_node and no_intersects:
            nodes_df.loc[row.out_node]['longitude'], nodes_df.loc[row.out_node]['latitude'] = new_out_node[0], new_out_node[1]
            if method == 'generate_nodes':
                cur.execute(f"INSERT INTO nodes VALUES ({last_node_id},{new_out_node[1]},{new_out_node[0]},{weight});")
                cur.execute(f"UPDATE edges SET out_node={last_node_id} WHERE id={row.id};")
                last_node_id += 1
            elif method == 'replace_nodes':
                cur.execute(f"UPDATE nodes SET latitude={new_out_node[1]}, longitude={new_out_node[0]} WHERE id={row.out_node};")
            print(f'out node of edge id: {row.id} changes')
    conn.commit()
    conn.close()

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, filter, and generate trajectories from raw GPD data')
    parser.add_argument('--map_dbpath', type=str, help='Path to map sqlite database file')
    parser.add_argument('--method', type=str, help='method to generate new edges and node sets')
    args = parser.parse_args()

    postprocess(args.map_dbpath, args.method)