function s = topologyLink3(s, link_dist, is_plot)
if nargin<3
    is_plot = false;
end

nodes = topologyLineVertexs(s,0);
% az = csu_azimuth( nodes(:,[2,3]), nodes(:,[4,5]) );
nodes =[ [nodes(:,2:3); nodes(:,4:5)], ...
    [nodes(:,1); nodes(:,1)], ...
    [ones(size(nodes,1),1); 2*ones(size(nodes,1),1)] ];

[~, kd] = knnsearch(nodes(:,1:2), nodes(:,1:2), 'k', 2);

tol = 10^(-3);
kd = nodes( kd(:,2) > tol, [3, 4]);  % [roadId, type==1]

%%%%%%%%%%%%%%%%%%5
if is_plot
    figure;plotmap(s);hold on;drawnow;
end

p = isnan(s(1).X(end));
for i=1:size(kd,1)
    id = kd(i,1);
    if kd(i,2)==1
        % head
        X = [s(id).X(1), s(id).Y(1)];
        d = sqrt( (X(1)-nodes(:,1)).^2+(X(2)-nodes(:,2)).^2 );
        
        ind = (d <= link_dist) & (nodes(:,3) ~= id);
        
        if any(ind)
            d = d(ind);
            nid = find(ind);
            [~, J] = min(d);
            ct = nodes(nid(J), 1:2);
            
            if is_plot
                plot(s(id).X, s(id).Y, 'c-', 'linewidth',3);
                plot(ct(1),ct(2), 'ro','markersize',12);
                drawnow;
            end
            
            s(id).X = [ct(1), s(id).X(1:end-p)];
            s(id).Y = [ct(2), s(id).Y(1:end-p)];
        end
        
    else
        % tail
        X = [s(id).X(end-p), s(id).Y(end-p)];
        d = sqrt( (X(1)-nodes(:,1)).^2+(X(2)-nodes(:,2)).^2 );
        
        ind = (d <= link_dist) & (nodes(:,3) ~= id);
        
        if any(ind)
            d = d(ind);
            nid = find(ind);
            [~, J] = sort(d, 'ascend');
            ct = nodes(nid(J), 1:2);
            
            if is_plot
                plot(s(id).X, s(id).Y, 'c-', 'linewidth',3);
                plot(ct(1),ct(2), 'ro','markersize',12);
                drawnow;
            end
            
            s(id).X = [s(id).X(1:end-p), ct(1)];
            s(id).Y = [s(id).Y(1:end-p), ct(2)];
        end
    end
    
    if p>0
        if ~isnan(s(id).X(end))
            s(id).X = [s(id).X , NaN];
            s(id).Y = [s(id).Y , NaN];
            
            if is_plot
                plot(s(id).X, s(id).Y, 'r-','linewidth',3);drawnow;
            end
        end
    end
    
    
    
end

end %



