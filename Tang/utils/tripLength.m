function len = tripLength(T)
n = length(T);
len = zeros(n,1);
flag = isnan( T(1).X(end) );

if flag
    for i=1:n
        len(i) = sum( sqrt((T(i).X(2:end-1)-T(i).X(1:end-2)).^2 + ...
            (T(i).Y(2:end-1)-T(i).Y(1:end-2)).^2) );
    end
else
    for i=1:n
        len(i) = sum( sqrt((T(i).X(2:end)-T(i).X(1:end-1)).^2 + ...
            (T(i).Y(2:end)-T(i).Y(1:end-1)).^2) );
    end
end

