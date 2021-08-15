function tripGPS2Biagioni(gpsdata_or_trips, output_trips_path)
% 将GPS轨迹点数据(CarID, Lon, Lat, Time,Dir,Speed,IsBusy)转换为Biagioni_Eriksson map construction程序
% 可以处理的trip_#.txt输入文件
%

X_Y_TIME_INDEX = [1,2,3]; % [X,Y,Time]

if ~exist(output_trips_path, 'dir')
    mkdir(output_trips_path);
end


count = -1;
skip_index = 100000;
min_nodes_num = 5;  % 每一条轨迹最少包含的点数目

if ischar(gpsdata_or_trips)
    % trips: Ahmed used format, <X,Y,TIME>
    fs = dir([gpsdata_or_trips, '/*.txt']);
    for i=1:length(fs)
        nodes = importdata([gpsdata_or_trips, '/', fs(i).name]);
        nodes = nodes(:, X_Y_TIME_INDEX);
        
        nodes_nums = size(nodes,1);
        if nodes_nums >= min_nodes_num
            count = count + 1;
            nodeid = skip_index*(count + 1) + 1;
            
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

else
    % gps point matrix
    GPSTIME_IND = 4;
    gpsdata_or_trips(:,GPSTIME_IND) = round(( gpsdata_or_trips(:,GPSTIME_IND) - min(gpsdata_or_trips(:,GPSTIME_IND)) )*(24*60*60));
    carId = gpsdata_or_trips(:,1);
    Id = unique( carId );
    
    for i=1:length(Id)
        nodes = gpsdata_or_trips(carId==Id(i), [2,3,4]);
        nodes_nums = size(nodes,1);
        if nodes_nums >= min_nodes_num
            count = count + 1;
            nodeid = skip_index*(count + 1) + 1;
            
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
end

end %


