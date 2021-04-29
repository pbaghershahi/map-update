The map updating algorithm has three steps:
1- Preprocess and generate trajectories

2- Matching trajectories to ground truth map to identify unmatch trajectories. We make use of an algorithm based on
Hidden Markov Model (HMM) which is called Fast Map Matching (FMM).

3- Inferring map graph from unmatch trajectories. First we made use of an algorithm based on clustering which is
called COBWEB, but because of its undesirable results, this algorithm has been left behind. Finally we take
advantage of an algorithm based on Kernel Density Estimation (KDE) which presents appropriate results. Both algorithm's
implementations are available but here we have just prepared a guide to KDE method. You can access the COBWEB method
implementation at "cobweb" directory.

To test the algorithm and make results you just have to put parquet data files of each day in the specified directories at ./data/gps-data/<day>.
Also you would need to to install fmm package for map matching phase; There is a complete instruction on how to install the package prepared at matching/main.py
Other essential packages are listed at the report.
Please save the created directories if you want to follow the instructions bellow, otherwise make sure that you have created needed paths.

###################### Preprocess and Generation ##########################
1- Input desired area bounding box bounding_box.txt

2- Load ground truth map from database (openstreetmap https://www.openstreetmap.org/)
python ground-map/ground_map.py --bounding_box_path ./utils/bounding_box.txt --ground_map_path ./ground-map/map/all_edges.shp --filtered_map_path ./ground-map/map/filtered_edges.shp --dropped_map_path ./ground-map/map/dropped_edges.shp

3- Preprocess and generate trajectories (to csv and shape file formats).
python traj_generator.py --bounding_box_path ./utils/bounding_box.txt --data_directory ./data/gps-data/ --csv_output_directory ./data/gps-csv/ --shape_output_directory ./data/trajectories/trajs.shp --from_directory True --has_distance True

############################# Map Matching #################################
1- Match edges as trajectories with the existing filtered ground truth map to detect overlapping edges
python matching/match.py --ground_map_path ./ground-map/map/filtered_edges.shp --trajs_path ./data/inferred-edges/edges.shp --add_score True --save_unmatched True --write_opath True --output_file_path ./data/mr.csv --radius 20 --gps_error 20 --n_edge_split 9 --overlap_portion 0.5

To evaluate the algorithm performance we should also pass two following steps
2- Match trajectories with the existing ground truth map to detect edges which have at least n trajectories passing through them
python matching/match.py --ground_map_path ./ground-map/map/all_edges.shp --trajs_path ./data/trajectories/trajs.shp --output_file_path ./data/trajs_mr.csv --write_opath True --radius 100 --gps_error 40
3- Match not overlapped edges with dropped edges to detect the right and wrong detected edges to compute precision, recall, and f1-score
python matching/match.py --ground_map_path ./ground-map/map/dropped_edges.shp --trajs_path ./data/unmatched.shp --add_score True --output_file_path ./data/unmatched_mr.csv --write_opath True --radius 60 --gps_error 40 --n_edge_split 9 --overlap_portion 0.33

############################ Map Inference #################################
1- Create KDE (kde.png) from trips
python kde/kde.py --trajs_path ./data/gps-csv/ --kde_output_path ./results/kde/kde.png --raw_output_path ./results/kde/raw_data.png --bounding_box_path ./utils/bounding_box.txt

2- Create grayscale skeleton from KDE
python kde/skeleton.py --input_image_file ./results/kde/kde.png --output_image_file ./results/kde/skeleton.png --output_skeleton_dir ./results/kde/skeleton-images/ --closing_radius 6

3- Extract map database from grayscale skeleton
python kde/graph_extract.py --skeleton_image_path ./results/kde/skeleton.png --bounding_box_path ./utils/bounding_box.txt --output_file_path ./results/kde/skeleton-maps/skeleton_map_1m.db

4- Map-match trips onto map database
python kde/graphdb_matcher_run.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1m.db --trajs_path ./data/gps-csv/ --match_output_path ./results/kde/first-matches/

5- Prune map database with map-matched trips, producing pruned map database
python kde/process_map_matches.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1m.db --match_trajs_path ./results/kde/first-matches/ --processed_map_path ./results/kde/skeleton-maps/skeleton_map_1p.db

6- Refine topology of pruned map, producing refined map
python kde/refine_topology.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1p.db --match_trajs_path ./results/kde/skeleton-maps/skeleton_map_1p_traces.txt --processed_map_path ./results/kde/skeleton-maps/skeleton_map_1r.db

7- Map-match trips onto refined map
python kde/graphdb_matcher_run.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1r.db --trajs_path ./data/gps-csv/ --match_output_path ./results/kde/second-matches/

8- Prune refined map with map-matched trips, producing pruned refined map database
python kde/process_map_matches.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1r.db --match_trajs_path ./results/kde/second-matches/ --processed_map_path ./results/kde/skeleton-maps/skeleton_map_2p.db

9- Output pruned refined map database for visualization
python kde/streetmap.py --file_type graphdb --input_graph_file ./results/kde/skeleton-maps/skeleton_map_2p.db --output_map_file ./results/kde/final_map.txt

10- Plot the last step generated map
python kde/plot_map.py

############################# evaluate KDE inferred map ##############################
To just evaluate the inferred map you should run the below command
python kde/evaluation.py --ground_map_path ./ground-map/map/all_edges.shp --infer_map_dbpath ./results/kde/skeleton-maps/skeleton_map_1m.db

############################## create unmatched csv file #############################
To read the unmatched trajectories from unmatched file and write the unmatched GPS file run the below command
python main.py --matches_file_path ../data/mr.csv --output_directory ./data/unmatch --data_directory ../data/gps-csv/

######################### create trajectories from edges #############################
To create trajectories from inferred edges in shape format (.shp) run the below command
python edge_traj.py --map_dbpath ./results/kde/skeleton-maps/skeleton_map_1m.db --shape_output_path ./data/inferred-edges/edges.shp --n_edge_splits 9 --min_length 20


python evaluation.py --match_path ./data/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path ./data/inferred-edges/edges.shp --dropped_map_path ./ground-map/map/dropped_edges.shp --results_save_path ./evaluation_results.txt
python plot.py --match_path ./data/unmatched_mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path ./data/inferred-edges/edges.shp --dropped_map_path ./ground-map/map/dropped_edges.shp --filtered_map_path ./ground-map/map/filtered_edges.shp --figure_save_path ./unmatched_dropped.png --apply_cos_sim True
python plot.py --match_path ./data/mr.csv --trajs_match ./data/trajs_mr.csv --inferred_edges_path ./data/inferred-edges/edges.shp --dropped_map_path ./ground-map/map/dropped_edges.shp --filtered_map_path ./ground-map/map/filtered_edges.shp --figure_save_path ./unmatched_dropped.png --plot_matches True