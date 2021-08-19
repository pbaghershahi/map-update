function s = tripRead(trips_path)
tf = dir([trips_path, '/*.csv']);
trips_num = length(tf);
disp('here in trip read function');

s = struct;

all_trips = [];
c = 1;

for i=1:trips_num
	disp('here');
	temp_file = csvread([trips_path, '/', tf(i).name], 1, 0);
	temp_trip = [];
	t1_size = size(temp_file);
	for j=1:t1_size(1)-1
		try
			temp_trip = [temp_trip; temp_file(j, :)];
			if temp_file(j, 1) ~= temp_file(j+1, 1)
				t2_size = size(temp_file);
				if t2_size(1) > 1
					s(c).X = temp_trip(:, 2)';
					s(c).Y = temp_trip(:, 3)';
					s(c).Time = temp_trip(:, 5)/1000';
					s(c).Id = temp_trip(1, 1);
					c = c+1;
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
s = s(I)';

end %
