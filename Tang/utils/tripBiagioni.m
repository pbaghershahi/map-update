function tripBiagioni(wgs_trace, trips, output_trips_path)
if ~exist(output_trips_path, 'dir')
    mkdir(output_trips_path);
end

count = -1;
skip_index = 100000;
min_nodes_num = 3;  % 每一条轨迹最少包含的点数目

% gps point matrix
min_gps_time = min([trips.Time]);

for i=1:length(wgs_trace)
    x = wgs_trace(i).X(1:end-1);
    y = wgs_trace(i).Y(1:end-1);
    t = trips(i).Time;
    nodes = [x(:), y(:), t(:)];
    nodes_nums = size(nodes,1);
    if nodes_nums >= min_nodes_num
        count = count + 1;
        nodeid = skip_index*(count + 1) + 1;
        nodes(:,3) = nodes(:,3) - min_gps_time;
        
        fid = fopen(fullfile(output_trips_path, ['trip_', num2str(count), '.txt']), 'w');
        
        fprintf(fid, '%d,%.6f,%.6f,%.1f,%s,%d\r\n',...
            nodeid, nodes(1,2), nodes(1,1), nodes(1,3), 'None', nodeid+1);
        
        for j=2:(nodes_nums-1)
            nodeid = nodeid + 1;
            fprintf(fid, '%d,%.6f,%.6f,%.1f,%d,%d\r\n',...
                nodeid, nodes(j,2), nodes(j,1), nodes(j,3), nodeid-1, nodeid+1);
        end
        
        nodeid = nodeid + 1;
        fprintf(fid, '%d,%.6f,%.6f,%.1f,%d,%s\r\n',...
            nodeid, nodes(nodes_nums,2), nodes(nodes_nums,1), nodes(nodes_nums,3), nodeid-1, 'None');
        
        fclose(fid);
    end
end

