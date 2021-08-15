function s = topologyLink2(s, link_dist, cut_dist, is_plot)
if nargin<4
    is_plot = false;
end

X = topologyLineVertexs(s);
az = csu_azimuth( X(:,[2,3]), X(:,[4,5]) );
X =[ [X(:,2:3); X(:,4:5)], ...
    [X(:,1); X(:,1)], ...
    [ones(size(X,1),1); 2*ones(size(X,1),1)] ];

IDX = DBSCAN(X(:,1:2),link_dist,1);
c = unique(IDX(IDX>0));

p = isnan(s(1).X(end));

if is_plot
    figure;plotmap(s);hold on;drawnow;
end

for i=1:length(c)
    pt = X(IDX==c(i),:);
    % ct = mean(pt(:,[1,2]));
    ct = compute_linkpoint(pt, s(pt(:,3)), az(pt(:,3)));
    
    for j=1:size(pt,1)
        id = pt(j,3);
        
        if is_plot
            plot(s(id).X, s(id).Y, 'c-', 'linewidth',3);
            plot(ct(1),ct(2), 'ro','markersize',12);
            drawnow;
        end
        
        
        [xt,yt] = seg_cut(s(id).X(1:(end-p)), s(id).Y(1:(end-p)), cut_dist, pt(j,4));
        if pt(j,4)==1
            % head
            s(id).X = [ct(1), xt];
            s(id).Y = [ct(2), yt];
        else
            % tail
            s(id).X = [xt, ct(1)];
            s(id).Y = [yt, ct(2)];
        end
        
        if p>0
            if ~isnan(s(id).X(end))
                s(id).X = [s(id).X , NaN];
                s(id).Y = [s(id).Y , NaN];
            end
        end
        
        if is_plot
            plot(s(id).X, s(id).Y, 'r-','linewidth',3);drawnow;
            % pause(0.1);
            % delete([h1, h2, h3]);
        end
        
    end
end

% 删除首尾相连的线
n = length(s);
ind = false(n,1);
p = isnan(s(1).X(end));
tol = 10^(-3);
for i=1:n
    if abs(s(i).X(1)-s(i).X(end-p))<tol && abs(s(i).Y(1)-s(i).Y(end-p))<tol
        ind(i) = true;
    end
end
s(ind) = [];


% 删除两个首尾一样的道路中长度较长的那条
n = length(s);
ind = zeros(n,2);
count = 0;
p = isnan(s(1).X(end));
TOL = 10^(-6);
for i=1:(n-1)
    for j=(i+1):n
        d1 = (s(i).X(1)-s(j).X(1))^2 + (s(i).Y(1)-s(j).Y(1))^2;
        d2 = (s(i).X(1)-s(j).X(end-p))^2 + (s(i).Y(1)-s(j).Y(end-p))^2;
        if d1<TOL || d2<TOL
            d3 = (s(i).X(end-p)-s(j).X(1))^2 + (s(i).Y(end-p)-s(j).Y(1))^2;
            d4 = (s(i).X(end-p)-s(j).X(end-p))^2 + (s(i).Y(end-p)-s(j).Y(end-p))^2;
            if d3<TOL || d4<TOL
                count = count + 1;
                ind(count,:) = [i,j];
            end
        end
    end
end
ind = ind(1:count,:);
if ~isempty(ind)
    I = tripLength(s(ind(:,1))) > tripLength(s(ind(:,2)));
    ind  = unique([ind(I,1); ind(~I,2)]);
    s(ind) = [];
end
end %



%%
function [xt,yt] = seg_cut(x, y, cut_distance, is_cut_from_tail)
if isempty(cut_distance) || cut_distance < 0
    if is_cut_from_tail==2
        xt = x(1:end-1);
        yt = y(1:end-1);
    else
        xt = x(2:end);
        yt = y(2:end);
    end
    return;
end


% 从尾部将曲线(x,y)裁剪掉cut_distance
if is_cut_from_tail == 2
    x = fliplr(x);
    y = fliplr(y);
end

I = 0;
d = cut_distance;
for i=1:length(x)-1
    d = d - sqrt((x(i)-x(i+1))^2 + (y(i)-y(i+1))^2);
    if d <= 0
        I = i;
        break;
    end
end
if I==0
    xt = [];
    yt = [];
else
    r = (-d) / sqrt( (x(I+1)-x(I))^2 + (y(I+1)-y(I))^2 );
    x0 = x(I+1) - ( x(I+1)-x(I) )*r;
    y0 = y(I+1) - ( y(I+1)-y(I) )*r;
    
    xt = [x0, x(I+1:end)];
    yt = [y0, y(I+1:end)];
    
    if is_cut_from_tail == 2
        xt = fliplr(xt);
        yt = fliplr(yt);
    end
end
end %



%%
function ct = compute_linkpoint(pt, s, az)
dir_threshold = 55;
p = 0;
if isnan(s(1).X(end))
    p = 1;
end

if size(pt,1)==2
    z1 = az(1);
    z2 = az(2);
    
    if pt(1,4)==1
        x1=s(1).X(1);
        y1=s(1).Y(1);
    else
        x1=s(1).X(end-p);
        y1=s(1).Y(end-p);
    end
    if pt(2,4)==1
        x2=s(2).X(1);
        y2=s(2).Y(1);
    else
        x2=s(2).X(end-p);
        y2=s(2).Y(end-p);
    end
    
    if abs(cos(z1-z2)) <= abs(cos(dir_threshold/180*pi))
        % 垂直交叉
        y0 = (x2-x1+y1*tan(z1)-y2*tan(z2))/(tan(z1)-tan(z2));
        x0 = x1+(y0-y1)*tan(z1);
    else
        x0 = (x1+x2)/2;
        y0 = (y1+y2)/2;
    end
    ct = [x0,y0];
else
    ct = median(pt(:,[1,2]));
end
end %





