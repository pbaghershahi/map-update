function segments = topologyLineSplit(s)
segments = [];

p = isnan(s(1).X(end));
n = length(s);
for i=1:n   
    xv = s(i).X(1:end-p);
    yv = s(i).Y(1:end-p);
    
    ind = true(1,n);
    ind(i) = false;
    
    [x, y] = topologyCut(xv, yv, [s(ind).X], [s(ind).Y]);
    segment = struct('X', cell(length(x),1), 'Y', cell(length(x),1));
    for k=1:length(x)
        segment(k).X = [x{k}, NaN];
        segment(k).Y = [y{k}, NaN];
    end
    segments = [segments; segment];
end

% 
len = tripLength(segments);
segments = addfield(segments, 'length', len);
segments(len<10^(-3)) = [];

n = arrayfun(@(x) length(x.Y), segments) - isnan(segments(1).X(end));
segments(n<2) = [];





