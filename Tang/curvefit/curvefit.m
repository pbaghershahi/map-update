function map = curvefit(geo, IDX, knots_nums, minpts, is_change)
if nargin<5
    is_change = true;
end

if nargin<4
    minpts = 3;
end

if nargin<3
    knots_nums = 4;
end

IDX = rmcluster(IDX, minpts);

classid = unique(IDX(IDX>0));
m = length(classid);

map = struct('X', cell(m,1), 'Y', cell(m,1));

count = 0;
for i=1:m
    X = geo(IDX==classid(i),1:2);
    
    % Piecewise linear fitting
    kn = knots_nums;
    pointnum = size(X,1);
    d = bsxfun(@minus, X, mean(X,1));
    d = max( sqrt(sum(d.^2, 2)) );
    
    if is_change
        if d <300 || pointnum<20
            kn = 4;
        end
        if d <150 || pointnum<10
            kn = 3;
        end
        if d <50 || pointnum<5
            kn = 2;
        end
    end
    
    
    % S1:
    %{
    [xf, yf] = piecewise_linear(X(:,1), X(:,2), kn);
    cvline(i).X = xf(:)';
    cvline(i).Y = yf(:)';
    %}
    
    %S2:
    % {
    [xf, yf] = lsq_piecewise(X(:,1), X(:,2), kn);
    if ~isempty(xf)
        count = count + 1;
        map(count).X = [xf', NaN];
        map(count).Y = [yf', NaN];
    end
    %}

    % fprintf('    have processed the class #%4d/%d \n', i, m);
end
map = map(1:count);
% fprintf('    done. \n');

% mat2shp(fullfile(path,[name, '.shp']), map, [], prj);

end %


