#!/usr/bin/env python
# encoding: utf-8


"""
 File: parameter_sensitive.py
 Version: Python2.7
 Time: 2018-12-14 16:20
"""


import os
import arcpy

workspace = "G:/GPS/out/"
if not os.path.exists(workspace):
    os.mkdir(workspace)

arcpy.env.overwriteOutput = True
arcpy.env.workspace = workspace

# Calculate the sum length of roads
def calculate_map_sumlength(shpfile_path):
    sum_length = 0.00

    fieldlist = arcpy.ListFields(shpfile_path)
    is_already_has = False
    global fileName
    fileName = "Length"
    for fd in fieldlist:
        if str(fd.name) == "Length":
            is_already_has = True
            fileName = "Length"
            break
        elif str(fd.name) == "length":
            is_already_has = True
            fileName = "length"
            break


    if not is_already_has:
        arcpy.AddField_management(shpfile_path, "Length", "DOUBLE", 20, 20)

    arcpy.CalculateField_management(shpfile_path,
                                    fileName,
                                    "!shape.length@unknown!", "PYTHON_9.3")
    cursor = arcpy.SearchCursor(shpfile_path)
    for row in cursor:
        sum_length = sum_length + float(row.getValue(fileName))

    return sum_length


def create_buffer(roadmap, output_path, name, buffer_dists):
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    for d in buffer_dists:
        buffer_map =  output_path + "%s_%d.shp" % (name, d)
        arcpy.Buffer_analysis(roadmap, buffer_map,d)


# Calculate the assesement measures
def calculate_matching_fscore(ground_truth_map, ground_truth_map_buffer,
                              ground_map_length,
                              reconstructed_map, reconstructed_map_buffer,
                              reconstructed_map_length):

    re_matched_map = workspace + "clip1.shp"
    arcpy.Clip_analysis(reconstructed_map, ground_truth_map_buffer, re_matched_map)
    re_matched_map_length = calculate_map_sumlength(re_matched_map)

    gt_matched_map = workspace + "clip2.shp"
    arcpy.Clip_analysis(ground_truth_map, reconstructed_map_buffer, gt_matched_map)
    gt_matched_map_length = calculate_map_sumlength(gt_matched_map)

    completeness = gt_matched_map_length / ground_map_length
    correctness  = re_matched_map_length / reconstructed_map_length
    fscore = 2 * completeness * correctness / (completeness + correctness)
    return fscore, correctness, completeness


def main(roadmap_path, datasets, parameters, match_distances):

    for data in datasets:
        ground_truth_map = roadmap_path + data + "/groundtruth.shp"
        ground_map_length = calculate_map_sumlength(ground_truth_map)
        gr_buffer_name = "ground_buffer"
        print("creating buffers of ground truth map...")
        create_buffer(ground_truth_map, workspace, gr_buffer_name, match_distances)
        print("done.")

        fscore_out = open(roadmap_path + data + "_param_Fscore.txt", 'w')
        fscore_out.write("Parameter  md=5  md=10  md=15  md=25" + '\r\n')
        precision_out = open(roadmap_path + data + "_param_Precision.txt", 'w')
        precision_out.write("Parameter  md=5  md=10  md=15  md=25" + '\r\n')
        recall_out = open(roadmap_path + data + "_param_Recall.txt", 'w')
        recall_out.write("Parameter  md=5  md=10  md=15  md=25" + '\r\n')

        for param in parameters:
            reconstructed_map = roadmap_path + data + "/%s/finalmap.shp" % param
            reconstructed_map_lenngth = calculate_map_sumlength(reconstructed_map)
            print("    creating buffers of map genertaed at %s..." % param)
            re_buffer_name = "param_buffer"
            create_buffer(reconstructed_map, workspace, re_buffer_name, match_distances)
            print("    done.")

            fscore_out.write(param + " ")
            precision_out.write(param + " ")
            recall_out.write(param + " ")

            for  match_dist in match_distances:
                ground_truth_map_buffer = workspace + "%s_%d.shp" % (gr_buffer_name, match_dist)
                reconstructed_map_buffer= workspace + "%s_%d.shp" % (re_buffer_name, match_dist)
                fscore = calculate_matching_fscore(ground_truth_map, ground_truth_map_buffer,
                                                   ground_map_length,
                                                   reconstructed_map, reconstructed_map_buffer,
                                                   reconstructed_map_lenngth)
                print("dataset: %s, match_distance: %.2f, parameter: %s" % (data, match_dist, param))
                print("    F: %.5f, P: %.5f, R: %.5f" % (fscore[0], fscore[1], fscore[2]))

                fscore_out.write("%.6f " % (fscore[0]))
                precision_out.write("%.6f " % (fscore[1]))
                recall_out.write("%.6f " % (fscore[2]))

            fscore_out.write('\r\n')
            precision_out.write('\r\n')
            recall_out.write('\r\n')

        fscore_out.close()
        precision_out.close()
        recall_out.close()


if __name__ == '__main__':
    map_path = "G:/GPS/parameter_sensitive/"

    # dataset = ["athens", "berlin", "chicago", "d1", "d2", "d3"]
    # dataset = ["chicago", "d1", "d2", "d3"]
    dataset = ["chicago", "d3"]
    # groundtruth_map = "groundtruth.shp"

    parameter = ["angle=5", "angle=10", "angle=15",
                 "angle=25", "angle=30", "angle=35",
                 "angle=40", "angle=45", "angle=50",
                 "angle=55", "angle=60", "angle=65",
                 "angle=70"]
    # reconstructed_map_name = "finalmap.shp"

    match_distance = [5, 10, 15, 25]
    main(map_path, dataset, parameter, match_distance)

