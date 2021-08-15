function nodes = topologyLineVertexs(s, is_two_column)
if nargin<2
    is_two_column = false;
end

line_num = length(s);
nodes = zeros(line_num, 5);

p = isnan(s(1).X(end));
if p
    for i=1:line_num
        nodes(i,:) = [i, s(i).X(1), s(i).Y(1), s(i).X(end-1), s(i).Y(end-1)];
    end
else
    for i=1:line_num
        nodes(i,:) = [i, s(i).X(1), s(i).Y(1), s(i).X(end), s(i).Y(end)];
    end
end



if is_two_column
    nodes =[ [nodes(:,2:3); nodes(:,4:5)], ...
        [nodes(:,1); nodes(:,1)], ...
        [ones(size(nodes,1),1); 2*ones(size(nodes,1),1)] ];
end

end %





