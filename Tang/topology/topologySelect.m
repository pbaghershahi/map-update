function map = topologySelect(map, min_dist, is_only_remove_hang)
if nargin<3
    is_only_remove_hang = true;
end

map = addfield(map, 'length', tripLength(map) );

TOL = 0.1;
if is_only_remove_hang
    vertexs = topologyLineVertexs(map, 1); % [x,y,seg_id,type(head==1)]
    [~, seg_id] = knnsearch(vertexs(:,1:2), vertexs(:,1:2), 'k', 2);
    seg_id = seg_id(:,2) > TOL;
    
    if ~isempty(seg_id)
        seg_id = unique(vertexs(seg_id,3));
        ind = [map(seg_id).length]' < min_dist;
        seg_id = seg_id(ind);
        
        map(seg_id) = [];
    end
else
    map = map([map.length] >= min_dist);
end


end  %


