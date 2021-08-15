function matched_map = tripMatching(trips_path, trips_type, roadmap_path)
% This script is to match the vehicle trips onto the ground truth maps.

% % 0. parameters
% match_trips_path = 'athens/trips/';
% match_map_path   = 'athen/map_athens_small.shp';

% 1. read the trip_x.txt file
match_trips = tripRead(trips_path, trips_type);

% 2. convert the trips into GPS points with direction, speed features
match_interp_dist = 20;  % meter
match_trips = tripTransform(match_trips, match_interp_dist);
match_trips = match_trips(:, [2,3,5]);

% 3. trip-map matching
map = shaperead(roadmap_path);
seg = mapSegments(map);
[~, spot] = gps_matching(match_trips(:,1:2), match_trips(:,3), seg, 40, 30);

matched_map = map(unique(seg(spot>1,5)));
clear match_trips_path  match_trips match_interp_dist match_groundmap_path match_map spot;




