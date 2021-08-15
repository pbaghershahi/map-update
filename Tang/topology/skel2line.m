function [map, BW2] = skel2line(BW, opts, knots_nums)

[height, width] = size(BW);
BW2 = false(size(BW)+2);
BW2(2:end-1,2:end-1) = BW;
[r,c] = find(BW2);

sz = size(BW2);
n = BW2(sub2ind(sz,r,c))+ ...
    BW2(sub2ind(sz,r-1,c-1))+ ...
    BW2(sub2ind(sz,r-1,c))+ ...
    BW2(sub2ind(sz,r-1,c+1))+ ...
    BW2(sub2ind(sz,r,c-1))+ ...
    BW2(sub2ind(sz,r,c+1))+ ...
    BW2(sub2ind(sz,r+1,c-1))+ ...
    BW2(sub2ind(sz,r+1,c))+ ...
    BW2(sub2ind(sz,r+1,c+1));
ind = n>3;
r = r(ind);
c = c(ind);
BW2(sub2ind(sz,r,c)) = false;
BW2 = BW2(2:end-1,2:end-1);

BW2 = bwlabel(BW2);
[r,c,label] = find(BW2);

n = max(label);
map = struct('X', cell(n,1), 'Y', cell(n,1));
ind = true(n,1);
for i=1:n
    map(i).X = c(label==i);
    if length(map(i).X)>=2
        %{
        map(i).Y = height - r(label==i);
        pts = DouglasPeucker([map(i).X, map(i).Y]', 10);
        map(i).X = pts(1,:);
        map(i).Y = pts(2,:);
        %}
        
        % {
        map(i).Y = height - r(label==i);
        
        map(i).X = map(i).X/opts.xscale + opts.boundingbox(1);
        map(i).Y = map(i).Y/opts.yscale + opts.boundingbox(2);
        
        knums = knots_nums;
        cxy = mean([map(i).X, map(i).Y]);
        if max((map(i).X-cxy(1)).^2+(map(i).Y-cxy(2)).^2)< (100^2)
            knums = 2;
        end
        
        [x,y] = lsq_piecewise(map(i).X, map(i).Y, knums);
        map(i).X = x';
        map(i).Y = y';
        %}
    else
        ind(i) = false;
    end
end
map=map(ind);



