function tripAhmed(trips, output_trips_path)
if ~exist(output_trips_path, 'dir')
    mkdir(output_trips_path);
end

min_gps_time = min([trips.Time]);

count = -1;
min_nodes_num = 3; % 每一条轨迹最少包含的点数目

for i=1:length(trips)
    d = [trips(i).X', trips(i).Y', trips(i).Time'];
    if size(d,1) >= min_nodes_num
        count = count + 1;
        d(:,3) = d(:,3) - min_gps_time ;
        fid = fopen(fullfile(output_trips_path, ['trip_', num2str(count), '.txt']), 'w');
        for j=1:size(d,1)
            fprintf(fid, '%.6f %.6f %.1f\r\n', d(j,1), d(j,2), d(j,3));
        end
        fclose(fid);
    end
end

