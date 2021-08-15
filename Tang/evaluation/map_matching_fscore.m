function [Fscore, spurious, missing] = map_matching_fscore(varargin)
%
%  map_matching_fscore(ground_truth_map_edge, ground_truth_map_node, constructed_map_edge, constructed_map_node, matching_dist,interp_dist)
%
%  map_matching_fscore(ground_truth_map, constructed_map, matching_dist,interp_dist)
%
%

if nargin==6
    % ground_truth_map_edge, ground_truth_map_node, constructed_map_edge, constructed_map_node, matching_dist
    ground_truth_map_edge_file = varargin{1};
    ground_truth_map_node_file = varargin{2};
    constructed_map_edge_file = varargin{3};
    constructed_map_node_file = varargin{4};
    matching_dist = varargin{5};
    interp_dist = varargin{6};
    
    disp('loading the ground truth map files: ');
    disp(['   edge - ', ground_truth_map_edge_file]);
    disp(['   node - ', ground_truth_map_node_file]);
    
    ground_map_edge = load(ground_truth_map_edge_file);
    ground_map_node = load(ground_truth_map_node_file);
    
    edge_num = size(ground_map_edge,1);
    ground_map = struct('X', cell(edge_num,1), 'Y', cell(edge_num,1), 'Id', cell(edge_num,1));
    for i=1:edge_num
        x = ground_map_node(ismember(ground_map_node(:,1),ground_map_edge(i,[2,3])), [2,3]);
        x = unique(x, 'rows');
        
        ground_map(i).X = x(:,1)';
        ground_map(i).Y = x(:,2)';
        ground_map(i).Id = ground_map_edge(i,1);
    end
    clear  ground_map_edge  ground_map_node  ground_truth_map_edge_file  ground_truth_map_node_file;
    
    disp('loading the constructed map files: ');
    disp(['   edge - ', constructed_map_edge_file]);
    disp(['   node - ', constructed_map_node_file]);
    
    constructed_map_edge = load(constructed_map_edge_file);
    constructed_map_node = load(constructed_map_node_file);
    
    edge_num = size(constructed_map_edge,1);
    constructed_map = struct('X', cell(edge_num,1), 'Y', cell(edge_num,1), 'Id', cell(edge_num,1));
    for i=1:edge_num
        x = constructed_map_node(ismember(constructed_map_node(:,1),constructed_map_edge(i,[2,3])), [2,3]);
        x = unique(x, 'rows');
        
        constructed_map(i).X = x(:,1)';
        constructed_map(i).Y = x(:,2)';
        constructed_map(i).Id = constructed_map_edge(i,1);
    end
    clear constructed_map_edge constructed_map_node constructed_map_edge_file constructed_map_node_file;
    
    
elseif nargin==4
    % ground_truth_map, constructed_map, matching_dist
    ground_map = varargin{1}; % map struct: 'X', 'Y' field
    constructed_map = varargin{2};
    matching_dist = varargin{3};
    interp_dist = varargin{4};
    
else
    error('input arguments is not correct.');
end

interp_dist = interp_dist/sqrt(2);  % to make the interp dist always work using 'interpm'
max_size = 100000;

holes   = zeros(max_size,2);
n = 0;
p = isnan(ground_map(1).X(end));
for i=1:length(ground_map)
    [x, y] = interpm(ground_map(i).X(1:end-p), ground_map(i).Y(1:end-p), interp_dist);
    npts = length(x);
    
    if size(holes,1) < (n+npts)
        holes = [holes; zeros(max_size, 2)];
    end
    
    holes( (n+1):(n+npts),: ) = [x(:), y(:)];
    n = n + npts;
end
holes = holes(1:n,:);


marbles = zeros(max_size,2);
n = 0;
p = isnan(constructed_map(1).X(end));
for i=1:length(constructed_map)
    [x, y] = interpm(constructed_map(i).X(1:end-p), constructed_map(i).Y(1:end-p), interp_dist);
    npts = length(x);
    
    if size(marbles,1) < (n+npts)
        marbles = [marbles; zeros(max_size, 2)];
    end
    
    marbles( (n+1):(n+npts),: ) = [x(:), y(:)];
    n = n + npts;
end
clear x y;
marbles = marbles(1:n,:);


[~, is_matched] = knnsearch(holes, marbles, 'K', 1);

is_matched = (is_matched <= matching_dist);
matched_marbles  = sum(is_matched);
spurious_marbles = sum(~is_matched);
spurious = spurious_marbles/(spurious_marbles+matched_marbles);
clear is_matched;

[~, is_empty] = knnsearch(marbles, holes, 'K', 1);

is_empty = (is_empty > matching_dist);
matched_holes  = sum(~is_empty);
empty_holes = sum(is_empty);
missing = empty_holes/(empty_holes+matched_holes);

Fscore = 2*(1-spurious)*(1-missing)/((1-spurious)+(1-missing));









