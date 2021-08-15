function [xb,yb] = geobuffer(x,y,bufwidth,varargin)
minx = min(x);
miny = min(y);
scale = 1000*max([max(y)-miny, max(x)-minx]);

x = (x-minx)./scale;
y = (y-miny)./scale;
bufwidth = bufwidth/scale;

[xb,yb] = bufferm(x,y,bufwidth,varargin{:});

xb = xb*scale + minx;
yb = yb*scale + miny;
