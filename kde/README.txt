The map updating algorithm has three steps:
1- Preprocess and generate trajectories

2- Matching trajectories to ground truth map to identify unmatch trajectories

3- Inferring map graph from unmatch trajectories

###################### Preprocess and Generation ##########################
1- Input desired area bounding box bounding_box.txt

2- Load ground truth map from database (openstreetmap https://www.openstreetmap.org/)
python ground-map/ground_map.py --bounding_box_path ./utils/bounding_box.txt --ground_map_path ./ground-map/map/all_edges.shp --filtered_map_path ./ground-map/map/filtered_edges.shp

3- Preprocess and generate trajectories (to csv and shape file formats)
python traj_generator.py --bounding_box_path ./utils/bounding_box.txt --data_directory ./data/gps-data/ --csv_output_directory ./data/gps-csv/ --shape_output_directory ./data/trajectories/trajs.shp

############################# Map Matching #################################
1- Match trajectories with existing ground truth map to detect unmatch trajectories
python matching/main.py --ground_map_path ./ground-map/map/all_edges.shp --trajs_path ./data/trajectories/trajs.shp --output_file_path ./data/mr.csv

############################ Map Inference #################################
1- Create KDE (kde.png) from trips
python kde/kde.py --trajs_path ./data/gps-csv/ --kde_output_path ./results/kde/kde.png --raw_output_path ./results/kde/raw_data.png

2- Create grayscale skeleton from KDE
python kde/skeleton.py --input_image_file ./results/kde/kde.png --output_image_file ./results/kde/skeleton.png --output_skeleton_dir ./results/kde/skeleton-images/

3) Extract map database from grayscale skeleton
python kde/graph_extract.py --skeleton_image_path ./results/kde/skeleton.png --bounding_box_path ./utils/bounding_box.txt --output_file_path ./results/kde/skeleton-maps/skeleton_map_1m.db

4) Map-match trips onto map database
python kde/graphdb_matcher_run.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1m.db --trajs_path ./data/gps-csv/ --match_output_path ./results/kde/first-matches/

5) Prune map database with map-matched trips, producing pruned map database
python kde/process_map_matches.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1m.db --match_trajs_path ./results/kde/first-matches/ --processed_map_path ./results/kde/skeleton-maps/skeleton_map_1p.db

6) Refine topology of pruned map, producing refined map
python kde/refine_topology.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1p.db --match_trajs_path ./results/kde/skeleton-maps/skeleton_map_1p_traces.txt --processed_map_path ./results/kde/skeleton-maps/skeleton_map_1r.db

7) Map-match trips onto refined map
python kde/graphdb_matcher_run.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1r.db --trajs_path ./data/gps-csv/ --match_output_path ./results/kde/second-matches/

8) Prune refined map with map-matched trips, producing pruned refined map database
python kde/process_map_matches.py --input_graph_file ./results/kde/skeleton-maps/skeleton_map_1r.db --match_trajs_path ./results/kde/second-matches/ --processed_map_path ./results/kde/skeleton-maps/skeleton_map_2p.db

9) Output pruned refined map database for visualization
python kde/streetmap.py --file_type graphdb --input_graph_file ./results/kde/skeleton-maps/skeleton_map_2p.db --output_map_file ./results/kde/final_map.txt