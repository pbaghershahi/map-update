function map = topologyStretch(s, extend_distance)
n = length(s);
map = struct('X', cell(n,1), 'Y', cell(n,1));

p = isnan(s(1).X(end));

for i=1:n
    x = s(i).X(1:end-p);
    y = s(i).Y(1:end-p);

    [x1, y1] = extend_polyline(x([2,1]), y([2,1]), extend_distance);
    [x2, y2] = extend_polyline(x((end-1):end), y((end-1):end), extend_distance);
    
    map(i).X = [x1, x, x2];
    map(i).Y = [y1, y, y2];
    
    if p>0
        map(i).X = [map(i).X, NaN];
        map(i).Y = [map(i).Y, NaN];
    end
    
end
end %


%%
function [xt,yt] = extend_polyline(x,y,extend_distance)
r = extend_distance / sqrt( (x(2)-x(1))^2 + (y(2)-y(1))^2 );
xt = x(2) + ( x(2)-x(1) )*r;
yt = y(2) + ( y(2)-y(1) )*r;
end % 



