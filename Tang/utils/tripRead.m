##function s = tripRead(trips_path, trips_type)
##tf = dir([trips_path, '/trip_*.txt']);
##trips_num = length(tf);
##
##s = struct('X', cell(trips_num,1), ...
##    'Y',cell(trips_num,1),...
##    'Time', cell(trips_num,1), ...
##    'Id', cell(trips_num,1));
##
##for i=1:trips_num
##	fid = fopen([trips_path, '/', tf(i).name]);
##	try
##		points = textscan(fid, '%f %f %f');
##		disp(points);
##		s(i).X = (points{1})'; % X
##		s(i).Y = (points{2})'; % Y
##		s(i).Time = (points{3})'; % time
##		s(i).Id = 1 + str2double( tf(i).name(6:end-4) );
##		
##	catch
##		fclose(fid);
##		error('read trips error.');
##	end
##	fclose(fid);
##end
####[~, I] = sort([s.Id]);
####s = s(I);
##
##
##end %

function s = tripRead(trips_path)
tf = dir([trips_path, '/*.csv']);
trips_num = length(tf);
disp('here in trip read function');

s = struct;

disp(s);
all_trips = [];
c = 1;

for i=1:trips_num
	disp('here');
	temp_file = csvread([trips_path, '/', tf(i).name], 1, 0);
	temp_trip = [];
	for j=1:size(temp_file)(1)-1
		try	
			temp_trip = [temp_trip; temp_file(j, :)];	
			if temp_file(j, 1) != temp_file(j+1, 1)
				if size(temp_trip)(1) > 1
					s(c).X = temp_trip(:, 2)';
					s(c).Y = temp_trip(:, 3)';
					s(c).Time = temp_trip(:, 5)';
					s(c).Id = temp_trip(1, 1);
					c++;
				end
				temp_trip = [];
			end
		catch
			disp('bad trajectory observed!');
			continue;
		end
	end
end

[~, I] = sort([s.Id]);
s = s(I);

end %
