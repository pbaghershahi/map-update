function I = topologyIsHangLine(map, tol)
if nargin<2
    tol = 10^(-3);
end

vertexs = topologyLineVertexs(map, 1); % [x,y,seg_id,type(head==1)]
[~, kd] = knnsearch(vertexs(:,1:2), vertexs(:,1:2), 'k', 2);
kd = vertexs( kd(:,2) > tol, 3);

I = false(length(map),1);
I(kd) = true;



