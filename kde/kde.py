import cv2
import sys, getopt
from location import TripLoader
from pylibs import spatialfunclib
from haversine import haversine, Unit
from itertools import tee
import numpy as np
import argparse, os
import imageio


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class KDE:
    def __init__(self):
        pass

    def create_kde_with_trips(self, all_trips):

        print("trips path: " + str(trips_path))
        print("cell size: " + str(cell_size))
        print("gaussian blur: " + str(gaussian_blur))

        diff_lat = max_lat - min_lat
        diff_lon = max_lon - min_lon

        # find scaling factor for longitude and latitude to meters
        width = int(haversine([max_lat, min_lon], [max_lat, max_lon], unit=Unit.METERS) / cell_size)
        height = int(haversine([min_lat, max_lon], [max_lat, max_lon], unit=Unit.METERS) / cell_size)
        yscale = height / diff_lat  # pixels per lat
        xscale = width / diff_lon  # pixels per lon

        themap = np.zeros((height, width), np.uint16)

        trip_counter = 1

        for trip in all_trips:

            if (trip_counter % 10 == 0) or (trip_counter == len(all_trips)):
                print("\rCreating histogram (trip " + str(trip_counter) + "/" + str(len(all_trips)) + ")... ")
            trip_counter += 1
            temp = np.zeros((height, width), np.uint8)

            limit = 400
            for (orig, dest) in pairwise(trip.locations):
                oy = height - int(yscale * (orig.latitude - min_lat))
                ox = int(xscale * (orig.longitude - min_lon))
                dy = height - int(yscale * (dest.latitude - min_lat))
                dx = int(xscale * (dest.longitude - min_lon))
                cv2.line(temp, (ox, oy), (dx, dy), 32, 1)

            temp16 = np.uint16(temp)
            themap = cv2.add(themap, temp16, themap)

        lines = np.zeros((height, width), np.uint8)

        print("done.")

        trip_counter = 1

        for trip in all_trips:

            if (trip_counter % 10 == 0) or (trip_counter == len(all_trips)):
                print("\rCreating drawing (trip " + str(trip_counter) + "/" + str(len(all_trips)) + ")... ")
            trip_counter += 1

            for orig, dest in pairwise(trip.locations):
                oy = height - int(yscale * (orig.latitude - min_lat))
                ox = int(xscale * (orig.longitude - min_lon))
                dy = height - int(yscale * (dest.latitude - min_lat))
                dx = int(xscale * (dest.longitude - min_lon))
                cv2.line(lines, (ox, oy), (dx, dy), 32, 1)

        # save the lines
        cv2.imwrite(raw_path, lines)

        print("done.")
        print("Smoothing... ")

        blur = cv2.GaussianBlur(themap, (gaussian_blur, gaussian_blur), 0)
        imageio.imwrite(kde_path, blur)

        print("done.")
        print("\nKDE generation complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hierarchical kernel density estimation on raw GPS trajectories')
    parser.add_argument('--cell_size', type=int, default=1, help='Cell size of each pixel in kde image (unit: meters)')
    parser.add_argument('--gaussian_blur', type=int, default=17, help='Gaussian kernel pixel size')
    parser.add_argument('--trajs_path', type=str, help='Path to gps trajectories')
    parser.add_argument('--bounding_box_path', type=str, help='Path to area bounding box')
    parser.add_argument('--kde_output_path', type=str, help='Path to save output kde image')
    parser.add_argument('--raw_output_path', type=str, help='Path to save raw trajectories output image')
    args = parser.parse_args()

    cell_size = args.cell_size
    gaussian_blur = args.gaussian_blur
    trips_path = args.trajs_path
    output_dir = '/'.join(args.kde_output_path.split('/')[:-1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    kde_path = args.kde_output_path
    raw_path = args.raw_output_path

    with open(args.bounding_box_path, 'r') as bbx_file:
        max_lat, min_lat, max_lon, min_lon = [float(line.strip('\n').split('=')[1]) for line in bbx_file]

    k = KDE()
    k.create_kde_with_trips(TripLoader.load_all_trips(trips_path))
