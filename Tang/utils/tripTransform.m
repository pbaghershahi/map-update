function gps = tripTransform(trips, deta_s)
gps = [];
if nargin<2
    deta_s = 50; % meters
end

for i=1:length(trips)
    x = trips(i).X;
    y = trips(i).Y;
    time = trips(i).Time;
    carId = trips(i).Id;
    
    pt = [x(1), y(1), time(1)];
    for j=1:(length(x)-1)
        kseg = ceil( sqrt((x(j+1)-x(j))^2+(y(j+1)-y(j))^2)/deta_s );
        
        if  kseg > 1
            xx = linspace(x(j),x(j+1),kseg+1);
            yy = linspace(y(j),y(j+1),kseg+1);
            tt = linspace(time(j),time(j+1),kseg+1);
            xx = xx(2:end);
            yy = yy(2:end);
            tt = tt(2:end);
        else
            xx = x(j+1);
            yy = y(j+1);
            tt = time(j+1);
        end
        pt = [pt; [xx(:), yy(:), tt(:)]];
    end
    clear xx yy tt x y time
    
    if size(pt,1) > 1
        dx = pt(2:end,1)-pt(1:end-1,1);
        dy = pt(2:end,2)-pt(1:end-1,2);
        
        az = pi/2 - atan2(dy, dx);
        ind = az<0;
        az(ind) = az(ind)+2*pi;
        az = [az; az(end)].*(180/pi);
        
        speed = (3.6).*sqrt(dx.^2 + dy.^2)./(pt(2:end,3)-pt(1:end-1,3));
        speed = [speed; speed(end)];
        
        gps = [gps; [carId*ones(length(az),1), pt, az, speed]];
    end
end

if ~isempty(gps)
    gps(:,4) = gps(:,4)./(60*60*24);
    gps(:,5) = round(gps(:,5));
end




