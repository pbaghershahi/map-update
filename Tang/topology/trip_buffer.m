function [BW, opts] = trip_buffer(map, buffersize, boundingbox)
warning off;
n = length(map);
% bf = struct('X', cell(n,1), 'Y', cell(n,1));

p = isnan(map(1).X(end));

figure('menubar','none', 'toolbar', 'none');
set(gcf, 'Visible', 'off');
axis off;
hold on;
for i=1:n
    %[xb, yb] = bufferm2('xy', map(i).X(1:end-p), map(i).Y(1:end-p), buffersize, 'out');
     
    [xb, yb] = geobuffer(map(i).X(1:end-p), map(i).Y(1:end-p), buffersize);

    % bf(i).X = xb(:)';
    % bf(i).Y = yb(:)';
    
    patch(xb, yb, [0.8 0.8 0.8], 'facecolor', 'k', 'edgecolor', 'k');
end
clear xb yb;
% clear bf;
buffersize = 2*buffersize;
boundingbox = [boundingbox(1)-buffersize, ...
    boundingbox(2)-buffersize, ...
    boundingbox(3)+buffersize, ...
    boundingbox(4)+buffersize];

set(gcf,'position', [0 0 840 630]);
set(gca,'xlim', boundingbox([1,3]), 'ylim', boundingbox([2,4]));
set(gca, 'position', [0 0 1 1]);

saveas(gcf, 'img.png');
close(gcf);

BW = rgb2gray(imread('img.png'));
BW = BW < 255;
% imwrite(BW, 'gis.png');

[height, width] = size(BW);
opts.xscale = width/(boundingbox(3)-boundingbox(1));
opts.yscale = height/(boundingbox(4)-boundingbox(2));
opts.boundingbox = boundingbox;

% sz = round(max(5*[opts.xscale, opts.yscale]));

BW = imclose(BW, strel('disk',2));
BW = imclose(BW, strel('disk',4));

BW = bwmorph(BW,'thin',Inf); 
%[3] Lam, L., Seong-Whan Lee, and Ching Y. Suen, 
%    "Thinning Methodologies-A Comprehensive Survey," 
%    IEEE Transactions on Pattern Analysis and Machine Intelligence, 
%    Vol 14, No. 9, September 1992, page 879.
% 

% figure; imshow(BW);

%{
sz = round(max(20*[opts.xscale, opts.yscale]));
se = strel('disk',sz);
BW = imclose(BW, se);
BW = bwmorph(BW,'thin',Inf);
%}
imwrite(BW, 'skel.png');

end % 


