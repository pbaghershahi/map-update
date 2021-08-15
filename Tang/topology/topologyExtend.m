function map = topologyExtend(s, cluster_dist, max_extend_dist, stretch_dist, is_plot)
if nargin<4
    stretch_dist = -1;
end
if nargin<5
    is_plot = false;
end

map = s;

if is_plot
    figure; plotmap(s); hold on %%%%%%%%%%%%%
end

X = topologyLineVertexs(map);
X =[ [X(:,2:3); X(:,4:5)], ...
    [X(:,1); X(:,1)], ...
    [ones(size(X,1),1); 2*ones(size(X,1),1)] ];

if cluster_dist <=0
    sId = DBSCAN(X,cluster_dist,1);
else
    sId = zeros(size(X,1),1);
end

%%%%%%%%%%%%%%%%%%%55
if is_plot
    scattx2(X(sId<1,1:2), 'marker',{'o'},'fill',0, 'color',{'r'},'markersize',10); drawnow;
end


sId = X(sId<1,[3,4]);
sId = sortrows(sId, 1);

clear s X;

p = isnan(map(1).X(end));

% 处理悬挂点（垂线端-延伸）
nums = length(map);
% is_hang = false(size(sId,1),1);

if nargin==4 && stretch_dist > 0
    map2 = topologyStretch(map, stretch_dist);
else
    map2 = map;
end

if ~isnan(map2(1).X(end))
    for i=1:length(map2)
        if ~isnan(map2(i).X(end))
            map2(i).X = [map2(i).X, NaN];
        end
    end
end

TOL = 10^(-3);
for i=1:size(sId,1)
    id = sId(i,1);
    
    %{
    if id==2 || id==36
        a = 1;
    end
    %}
    
    type = sId(i,2);
    
    [xt, yt] = stretch(map(id).X(1:end-p), map(id).Y(1:end-p), max_extend_dist, type==1);
    
    ind = true(1,nums);
    ind(id) = false;
    x = [map2(ind).X];
    y = [map2(ind).Y];
    
    [x0,y0] = polyintersect(xt, yt, x, y, TOL);
    clear x y ind;
    if isempty(x0) || isempty(y0)
        % is_hang(i) = true;
        continue;
    end
    
    if type==1
        % head
        if length(x0)>1
            pd = (x0-xt(2)).^2+(y0-yt(2)).^2;
            % {
            [~, ind] = min(pd);
            x0 = x0(ind);
            y0 = y0(ind);
            clear pd ind;
            %}            
        end
        
        if is_plot
            plot(x0,y0,'kx','markersize',10);drawnow;%%%%%%%%%%%%%%%%
        end
        
        if ( (x0-xt(1))*(x0-xt(2))<=0 ) && ( (y0-yt(1))*(y0-yt(2))<=0 )
            map(id).X = [x0, xt(2:end)];
            map(id).Y = [y0, yt(2:end)];
        end
        
    else
        % tail
        if length(x0)>1
            pd = (x0-xt(end-1)).^2+(y0-yt(end-1)).^2;
            [~, ind] = min(pd);
            x0 = x0(ind);
            y0 = y0(ind);
            clear pd ind;
            
            
        end
        
        if is_plot
            plot(x0,y0,'kx','markersize',10);drawnow;%%%%%%%%%%%%%%%%
        end
        
        if ( (x0-xt(end))*(x0-xt(end-1))<=0 ) && ( (y0-yt(end))*(y0-yt(end-1))<=0 )
            map(id).X = [xt(1:end-1), x0];
            map(id).Y = [yt(1:end-1), y0];
        end
        
    end
    
    if is_plot
        plot(map(id).X ,map(id).Y, 'r-','linewidth',3);drawnow;%%%%%%%%%%%%%%%%
    end
    
    if p>0
        if ~isnan(map(id).X(end))
            map(id).X = [map(id).X , NaN];
            map(id).Y = [map(id).Y , NaN];
        end
    end
end
end % 


function [xt,yt] = stretch(x, y, dis, is_from_head)

if is_from_head
    r = dis / sqrt( (x(2)-x(1))^2 + (y(2)-y(1))^2 );
    x0 = x(1) + ( x(1)-x(2) )*r;
    y0 = y(1) + ( y(1)-y(2) )*r;
    xt = [x0, x];
    yt = [y0, y];
else
    m = length(x);
    r = dis / sqrt( (x(m)-x(m-1))^2 + (y(m)-y(m-1))^2 );
    x0 = x(m) + ( x(m)-x(m-1) )*r;
    y0 = y(m) + ( y(m)-y(m-1) )*r;
    xt = [x, x0];
    yt = [y, y0];
end
end % 



