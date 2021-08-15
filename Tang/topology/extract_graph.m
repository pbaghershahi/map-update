function map = extract_graph(BW, opts, min_segment_len)
BW = BW>0;
height = size(BW,1);

BW2 = zeros(size(BW)+2);
BW2(2:end-1,2:end-1) = BW;
[I,J] = find(BW2);

image_size = size(BW2);
n = BW2(sub2ind(image_size,I,J))+ ...
    BW2(sub2ind(image_size,I-1,J-1))+ ...
    BW2(sub2ind(image_size,I-1,J))+ ...
    BW2(sub2ind(image_size,I-1,J+1))+ ...
    BW2(sub2ind(image_size,I,J-1))+ ...
    BW2(sub2ind(image_size,I,J+1))+ ...
    BW2(sub2ind(image_size,I+1,J-1))+ ...
    BW2(sub2ind(image_size,I+1,J))+ ...
    BW2(sub2ind(image_size,I+1,J+1));

ind = n>3;
I = I(ind);
J = J(ind);
BW2(sub2ind(image_size,I,J)) = 2;
BW2 = BW2(2:end-1,2:end-1);
[r, c] = find(BW2==2);
I = c;
J = height - r;

% figure; imagesc(BW2);

CC = bwconncomp(BW2==1);
n = CC.NumObjects;
map = struct('X',cell(n,1), 'Y',cell(n,1));
is_remove = true(n,1);

% figure; 
% hold on;
for i=1:n
    [r,c] = ind2sub(CC.ImageSize, CC.PixelIdxList{i});
    x = c;
    y = height - r;
    
%     plot(x,y,'bo');
%     drawnow;
    
    if length(x)>2
        [nn, dis] = fast_knnsearch([x,y], [], 2);
        order = [1, nn(1,1)];
        dis = dis(order,:);
        
        if dis(2,2) > dis(1,2)
            order = order([2, 1]);
        end
        
        nnid = nn(order(end),:);
        nnid = nnid(~ismember(nnid, order));
        while ~isempty(nnid)
            order = [order, nnid(1)];
            nnid = nn(order(end),:);
            nnid = nnid(~ismember(nnid, order));
        end
        
        nnid = nn(order(1),:);
        nnid = nnid(~ismember(nnid, order));
        while ~isempty(nnid)
            order = [nnid(1), order];
            nnid = nn(order(1),:);
            nnid = nnid(~ismember(nnid, order));
        end
        map(i).X = x(order)';
        map(i).Y = y(order)';
        
    else
        map(i).X = x';
        map(i).Y = y';
    end
    
%     plot(map(i).X, map(i).Y, 'y-');
%     drawnow;

    r = I;
    c = J;
    
    for k=1:2
        [d,ind] = min( (r-map(i).X(1)).^2+(c-map(i).Y(1)).^2 );
        if d <= 2.5
            map(i).X = [r(ind), map(i).X];
            map(i).Y = [c(ind), map(i).Y];

            
%             plot(r(ind), c(ind), 'rs', 'markersize',12);
%             drawnow;
            
            r(ind) = [];
            c(ind) = [];
        end
        
        [d,ind] = min((r-map(i).X(end)).^2+(c-map(i).Y(end)).^2);
        if d <= 2.5
            map(i).X = [map(i).X, r(ind)];
            map(i).Y = [map(i).Y, c(ind)];
            
%             plot(I(ind), J(ind), 'gs', 'markersize',12);
%             drawnow;
            
            r(ind) = [];
            c(ind) = [];
        end
    end
    map(i).X = map(i).X/opts.xscale + opts.boundingbox(1);
    map(i).Y = map(i).Y/opts.yscale + opts.boundingbox(2);
    
    if length(map(i).X) < 2
        is_remove(i) = false;
    end
end

map = map(is_remove);
link_dist = 3/opts.xscale;
map = topologyLink2(map, link_dist, 10, 0);
map = topologySelect(map, min_segment_len, 1);




