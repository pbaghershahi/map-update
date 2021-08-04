import pyximport; pyximport.install()
import subiterations
import numpy as np
import scipy.ndimage as nd
import imageio
from multiprocessing import Manager, cpu_count
from scipy.ndimage.morphology import grey_closing
import math

class GrayscaleSkeleton:
    def __init__(self):
        pass

    def skeletonize(self, image, closing_radius=8):
        out_image = grey_closing(image, footprint=circle(closing_radius), mode='constant', cval=0.0)
        out_image = add_zero_mat(out_image)
        prev_binary_image = np.zeros_like(out_image)

        image_bit_depth = (out_image.dtype.itemsize * 8) / 2
        print("image_bit_depth: " + str(image_bit_depth))

        image_thresholds = [2**x for x in range(int(image_bit_depth), 3, -1)] + list(range(15, 0, -1))
        print("image_thresholds: " + str(image_thresholds))

        for curr_threshold in image_thresholds:
            print("curr_threshold: " + str(curr_threshold))

            curr_thresh_image = np.clip(out_image, 0, curr_threshold)
            curr_binary_image = curr_thresh_image.astype(np.bool).astype(np.int)
            imageio.imwrite(skeleton_images_path + "binary_" + str(curr_threshold) + ".png", curr_binary_image)

            curr_sum_image = (prev_binary_image + curr_binary_image)
            curr_skeleton_image = self.thin_pixels(curr_sum_image)
            imageio.imwrite(skeleton_images_path + "skeleton_" + str(curr_threshold) + ".png", curr_skeleton_image)
            print("curr_skeleton max: " + str(curr_skeleton_image.max()))

            prev_binary_image = curr_skeleton_image

        return remove_zero_mat(prev_binary_image)

    def thin_pixels(self, image):
        pixel_removed = True

        neighbors = nd.convolve((image > 0).astype(np.int), [[1, 1, 1], [1, 0, 1], [1, 1, 1]], mode='constant', cval=0.0)
        fg_pixels = np.where((image == 1) & (neighbors >= 2) & (neighbors <= 6))
        check_pixels = list(zip(fg_pixels[0], fg_pixels[1]))
        out_image = image
        while len(check_pixels) > 0:
            out_image, sub1_check_pixels = self.parallel_sub(
                subiterations.first_subiteration, out_image, check_pixels
            )
            out_image, sub2_check_pixels = self.parallel_sub(
                subiterations.second_subiteration, out_image, list(set(check_pixels + sub1_check_pixels))
            )

            check_pixels = list(set(sub1_check_pixels+sub2_check_pixels))

        #Todo: check the following lines for indentation and
        # usage of neighbors and check for logic
        neighbors = nd.convolve(out_image>0,[[1,1,1],[1,0,1],[1,1,1]],mode='constant',cval=0.0)
        fg_pixels = np.where(out_image==1)
        check_pixels = list(zip(fg_pixels[0],fg_pixels[1]))
        out_image, _ = self.parallel_sub(self.empty_pools, out_image, check_pixels)
        return out_image

    def parallel_sub(self, sub_function, image, fg_pixels):
        manager = Manager()
        queue = manager.Queue()
        next_queue = manager.Queue()

        num_procs = int(math.ceil(float(cpu_count()) * 0.75))
        workload_size = int(math.ceil(float(len(fg_pixels)) / float(num_procs)))

        process_list = []

        if len(fg_pixels) == 0:
            return image, []
        zero_pixels, next_pixels = sub_function(image, fg_pixels)

        for x, y in zero_pixels:
            image[x][y] = 0

        return image, list(next_pixels)

    def empty_pools(self, curr_image, fg_pixels):
        zero_pixels = {}

        for i, j in fg_pixels:
            p2 = curr_image[i - 1][j]
            p3 = curr_image[i - 1][j + 1]
            p4 = curr_image[i][j + 1]
            p5 = curr_image[i + 1][j + 1]
            p6 = curr_image[i + 1][j]
            p7 = curr_image[i + 1][j - 1]
            p8 = curr_image[i][j - 1]
            p9 = curr_image[i - 1][j - 1]

            if bool(p2) + bool(p3) + bool(p4) + bool(p5) + bool(p6) + bool(p7) + bool(p8) + bool(p9) > 6:
                zero_pixels[(i, j)] = 0

        return zero_pixels, []


def add_zero_mat(image):
    num_rows, num_cols = image.shape

    out_image = np.insert(image, num_rows, np.zeros(num_cols, dtype=np.int), 0)
    out_image = np.insert(out_image, 0, np.zeros(num_cols, dtype=np.int), 0)

    num_rows, num_cols = out_image.shape

    out_image = np.insert(out_image, num_cols, np.zeros(num_rows, dtype=np.int), 1)
    out_image = np.insert(out_image, 0, np.zeros(num_rows, dtype=np.int), 1)

    return out_image

def remove_zero_mat(image):
    num_rows, num_cols = image.shape

    out_image = np.delete(image, num_rows - 1, 0)
    out_image = np.delete(out_image, 0, 0)
    out_image = np.delete(out_image, num_cols - 1, 1)
    out_image = np.delete(out_image, 0, 1)

    return out_image

def circle(radius):
    x, y = np.mgrid[:(2 * radius) + 1, :(2 * radius) + 1]
    circle_out = (x - radius) ** 2 + (y - radius) ** 2
    return (circle_out <= (radius ** 2)).astype(np.int)

import sys, time
import argparse, os


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Edge pruning on map graph')
    parser.add_argument('--input_image_file', type=str, help='Path to KDE image file')
    parser.add_argument('--output_image_file', type=str, help='Path to save skeleton image file')
    parser.add_argument('--output_skeleton_dir', type=str, help='directory to save skeleton images')
    parser.add_argument('--closing_radius', type=int, default=8, help='radius used for closing in skeletonization.')
    args = parser.parse_args()

    if not os.path.exists(args.output_skeleton_dir):
        os.makedirs(args.output_skeleton_dir)
    skeleton_images_path = args.output_skeleton_dir
    input_filename = args.input_image_file
    output_dir = '/'.join(args.output_image_file.split('/')[:-1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_filename = args.output_image_file

    print("input filename: " + str(input_filename))
    print("output filename: " + str(output_filename))

    input_kde = imageio.imread(input_filename)

    s = GrayscaleSkeleton()

    start_time = time.time()
    skeleton = s.skeletonize(input_kde, closing_radius=args.closing_radius)
    print("total elapsed time: " + str(time.time() - start_time) + " seconds")
    imageio.imwrite(output_filename, skeleton)
