function [cx, cy] = topologyCut(xv,yv,xcut,ycut)
% polyline裁剪

TOL = 10^(-6); % 判断x==y的精度限差

% [xI,yI] = curveintersect(xv, yv, xcut, ycut);
[xI,yI] = polyintersect(xv, yv, xcut, ycut, TOL);

if isempty(xI) || isempty(yI)
    cx = {xv};
    cy = {yv};
    return;
end

cx = [];
cy = [];
npts = length(xv);

for i=1:(npts-1)
    
    cx = [cx, xv(i)];
    cy = [cy, yv(i)];
 
    ind = ( (xI-xv(i)).^2+(yI-yv(i)).^2+(xI-xv(i+1)).^2+(yI-yv(i+1)).^2 ) - ...
        ( (xv(i)-xv(i+1))^2+(yv(i)-yv(i+1))^2 ) < TOL;
    
    x0 = xI(ind);
    y0 = yI(ind);
    
    if ~isempty(x0)
        r = sqrt( (x0-xv(i)).^2+(y0-yv(i)).^2 );
        [~, r] = sort(r);
        x0 = x0(r);
        y0 = y0(r);
        
        for j=1:length(x0)
            cx = [cx,x0(j),NaN,x0(j)];
            cy = [cy,y0(j),NaN,y0(j)];
        end
        
    end
end

cx = [cx, xv(end)];
cy = [cy, yv(end)];


ind = false(length(cx),1);
for i=1:length(cx)-1
    if (cx(i)-cx(i+1))^2+(cy(i)-cy(i+1))^2 < TOL
        ind(i+1) = true;
    end
end

cx(ind) = [];
cy(ind) = [];

[cx, cy] = polysplit(cx, cy);







