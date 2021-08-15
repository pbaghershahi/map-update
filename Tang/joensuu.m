% Main function to construct the road network map from GPS trips.
elipsed_time = tic;

trips_path   = [pwd, '\data\joensuu\'];
output_path = [pwd, '\results\joensuu\'];
if ~exist(output_path, 'dir')
    mkdir(output_path);
end

% parameters
interp_dist = 10;
min_road_len = 20;

%{
trips_path   = 'G:\Road\data\Chicago\trips\';     % input trips file path
curvefit_map_name = 'chicago_curvefit.shp';            % curve fitting (piecewise linear) result output file name
final_map_name    = 'chicago_constructed_map.shp';     % constructed final map name
%}


% Data pre-procesing
disp('setp1. data pre-procesing, please waitting ...');
library_path = genpath(pwd);
addpath( library_path );
% tic;
trip = tripRead(trips_path, 'biagioni');

% {
%将经纬度转换为UTM XY
for i=1:length(trip)   
    [X, m] = unique([trip(i).Y',trip(i).X'], 'rows');
    T = trip(i).Time(m);
    [T, I] = sort(T);
    X = X(I,:);
    
    [trip(i).X, trip(i).Y] = csu_latlon2utmXY(X(:,1)', X(:,2)');
    trip(i).Time = (T - min(T))/1000;  % second
    
    clear X T m I;
end
% figure; plotmap(trip);
%} END


% interp_dist = 50; 
option.interp_dist = interp_dist;
gps = tripTransform(trip, option.interp_dist);  % 以interp_dist(m)为间隔对轨迹进行插值
% toc;
clear trip;
disp('   done.');
disp(' ');

% call CDBSC clustering
disp('setp2. gps trace points clustering, please waitting ...');
% tic;
coord_direct_speed_index = [2,3,5,6]; % GPS点数据中X、Y、Direction(deg)、Speed(km/h)所在列
carid_index = 1; % GPS点数据中CarID所在列数

X = gps(:,coord_direct_speed_index); % GPS点数据[x,y,direction]
CarId = gps(:,carid_index);

% 0. 数据预处理
% max_speed = 100; % 最大速度阈值km/h
% min_speed = 5; % 最小速度阈值km/h
option.max_speed = 100;
option.min_speed = 0;    % for joensuu is walk, so the min speed is adjusted to zero

[~, m] = unique(X(:,1:2), 'rows');
X = X(m, :);
CarId = CarId(m);

m = X(:,4)>=option.min_speed & X(:,4)<=option.max_speed;
X = X(m,1:3);
CarId = CarId(m);
clear m  gps coord_direct_speed_index carid_index;

% 1. 计算空间邻域
% sigma = 3;         % Normalcut切割三角网长边的方差倍率
% max_length = 100;   % 三角网大于max_length的边都进行裁剪
% nn_k = 2;          % 空间邻域阶数（参考ASCDT）
sigma = 3;
max_length = 100;
nn_k = 2;
max_neighbor_diff = 10;
max_cluster_diff  = 15;
min_pts_num = 5;

E = graph_normalcut(X(:,1:3), [], sigma, max_length);
connect = graph_neighbors(E, nn_k, size(X,1), 1);
clear  E;

% 2. 空间聚类
option.neighbor_threshold = max_neighbor_diff;     % 相邻轨迹点之间的方向相似性阈值 (deg)
option.cluster_threshold  = max_cluster_diff;     % 同一个簇内的轨迹点方向相似性阈值 (deg)
option.spatial_threshold  = 20;     % 相邻轨迹点之间的横向距离（垂直于运动方向）阈值 m

% {
% clustering only consider the one way roads
IDX = CDBSC_abs(X(:,1:3), ...
    option.neighbor_threshold, ...
    option.cluster_threshold, ...
    option.spatial_threshold, [], ...
    connect);
%}

%{
% clustering consider the multiple way roads
IDX = CDBSC(gps(:,1:3), ...
    option.neighbor_threshold, ...
    option.cluster_threshold, ...
    option.spatial_threshold, [], ...
    connect);
%}


option.min_road_length = min_road_len;
option.min_pts_num = min_pts_num;
IX = prune_cluster(IDX, option.min_pts_num, X(:,1:2), option.min_road_length);
IX = merge_cluster(X, IX, connect, option.min_road_length/2, 45);
% toc;
clear prune_dist;
disp('   done.');
disp(' ');

save([output_path, 'cluster.mat'], 'X', 'CarId', 'connect', 'option', 'IDX', 'IX');
clearvars -except  X  IX final_map_name curvefit_map_name  option elipsed_time output_path;


% curve fitting
disp('setp3. curve fitting to generate road centerlines, please waitting ...');
% tic;
map = curvefit(X(:,1:2), IX, 6, option.min_pts_num);
boundingbox = [min(X(:,1:2)), max(X(:,1:2))];
% toc;
clear X IX;
mat2shp([output_path, 'curvefit.shp'], map);
disp('   done.');
disp(' ');



%% Topology refine
disp('setp4. topology refine, please waitting ...');
% map = shaperead(curvefit_map_name);
% tic;
len = tripLength(map);
map = addfield(map, 'len', len);
clear len;

m0 = map([map.len] >= option.min_road_length);

% figure; 
% plotmap(m0, 'linewidth', 2);
% set(gcf, 'name', 'Constructed map without topology refine', ...
%     'color', 'w');
% axis off;


% Topology
% 1. 将垂直延伸存在相交点的悬挂线进行延伸
option.max_extend_dist = 100; % 如果一条悬挂边距离其最近的垂直边小于该延长阈值，则将该悬挂线进行延伸至垂直点位置（以相邻道路间的垂直距离为参考进行设置）。
stretch_dist = 35; % 考虑到由于GPS定位存在误差，有些垂直的悬挂线在延伸的情况不相交，为此，对各悬挂线首先进行首尾的拉伸，该参数即为各路段首尾延伸的距离（以GPS定位误差进行设置）。

m1 = topologyExtend(m0, 0, option.max_extend_dist, stretch_dist, 0);

% set(gcf, 'name', 'Vertical extention refine', ...
%     'color', 'w');
% axis off;

%{
% 2. 将道路分割为相互连接的路段（其中，长度小于10^3的被删除）
m2 = topologyLineSplit(m1);

% 3. 删除小于一定长度的悬挂线路段
min_segment_length = option.min_road_length;
m3 = topologySelect(m2, min_segment_length, true);

% 4. 将交叉口处相交的悬挂线进行相连
option.max_link_dist = option.min_road_length/4;
m4 = topologyLink2(m3, option.max_link_dist, 30, 0);

% set(gcf, 'name', 'Node contraction refine', ...
%     'color', 'w');
% axis off;

toc;
%}


% {
buffersize = 15; % road buffer size (according to the GPS positioning error)
[BW, opts] = trip_buffer(m1, buffersize, boundingbox);

% m3 = skel2line(BW, opts, 3);
% option.max_link_dist = 50;
% m4 = topologyLink2(m3, option.max_link_dist, 20, 0);


% fid = fopen('boundingbox.txt', 'w');
% fprintf(fid, '%.6f %.6f %.6f %.6f', ...
%     opts.boundingbox(1), ...
%     opts.boundingbox(2), ...
%     opts.boundingbox(3), ...
%     opts.boundingbox(4) );
% fclose(fid);

m3 = extract_graph(BW, opts, 20);
m4 = topologyLineSimplify(m3, 1.0);
%}

figure; 
plotmap(m4, 'linewidth', 2); 
set(gcf, 'name', 'Final map', ...
    'color', 'w');
axis off;

disp('   done.');
disp(' ');

elipsed_time = toc(elipsed_time);

% Saving results
disp('setp4. saving the final updated map, please waitting ...'); 
save([output_path, 'finalmap.mat']);
mat2shp([output_path, 'finalmap.shp'], m4);

copyfile('img.png', output_path);
copyfile('skel.png', output_path);

disp('   done.');

fid = fopen([output_path, '\Elapsed_time.txt'], 'w');
fprintf(fid, 'Total elapsed time is %.4f second.', elipsed_time);
fclose(fid);

disp(['Total elapsed time is ', num2str(elipsed_time), ' second.']);






