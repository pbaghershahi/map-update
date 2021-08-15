function [xf, yf] = lsq_piecewise(x, y, knots_nums)
% LSQ_PIECEWISE Piecewise linear interpolation for 1-D interpolation (table lookup)
%   YI = lsq_piecewise( x, y, XI ) obtain optimal (least-square sense)
%   vector to be used with linear interpolation routine.
%   The target is finding Y given X the minimization of function 
%           f = |y-interp1(XI,YI,x)|^2
%   
%   INPUT
%       x measured data vector
%       y measured data vector
%       XI break points of 1-D table
%
%   OUTPUT
%       YI interpolation points of 1-D table
%           y = interp1(XI,YI,x)
% 
% Modified by Tang, 2018-03-10
% Copyright (c) 2013, Guido Albertin
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are
% met:
% 
%     * Redistributions of source code must retain the above copyright
%       notice, this list of conditions and the following disclaimer.
%

% if nargin<4
%     is_prune = false;
% end

x = x(:);
y = y(:);

if length(x) ~= length(y)
    error('Vector x and y must have dimension n x 1.');  
end

%%%%%%%%%%%%%%%%%%%%%%%%
x = [x, y];
% xy = sortrows(xy, [1,2]);

T = mean(x);
[R, x] = princomp(x);

%{
if is_prune
    %{
    ev = R(1,:)./sum(R(1,:));
    if ~any(ev >= 0.7)
        xf = [];
        yf = [];
        return;
    end
    %}
    
    %{
    if (max(x(:,2))-min(x(:,2)))/(max(x(:,1))-min(x(:,1))) > 0.7
        xf = [];
        yf = [];
        return;
    end
    %}
end
%}

y = x(:,2);
x = x(:,1);

%{
I = (x(2:end) - x(1:end-1))<eps;
if any(I)
    x(I) = x(I) - (10^(-5))*(sum(I):-1:1)';
end
%}

xf = linspace(min(x), max(x), knots_nums);
% xf = prctile(x, round(100*linspace(0,1,knots_nums)));
% xf = unique(xf);
xf = xf(:);
%%%%%%%%%%%%%%%%%%%%%%%%


% matrix defined by x measurements
A = sparse([]);

% vector for y measurements
Y = [];

for j=2:length(xf)
    
    % get index of points in bin [XI(j-1) XI(j)]
    ind = x>=xf(j-1) & x<xf(j);
    
    %{
    % check if we have data points in bin
    if ~any(ind)
        warning(sprintf('Bin [%f %f] has no data points, check estimation. Please re-define X vector accordingly.',xf(j-1),xf(j)));
    end
    %}
    
    % get x and y data subset
    x0 = x(ind);
    y0 = y(ind);
    
    % create temporary matrix to be added to A
    tmp = [(( -x0+xf(j-1) ) / ( xf(j)-xf(j-1) ) + 1) (( x0-xf(j-1) ) / ( xf(j)-xf(j-1) ))];
    
    % build matrix of measurement with constraints
    [m1,n1]=size(A);
    [m2,n2]=size(tmp);
    A = [[A zeros(m1,n2-1)];[zeros(m2,n1-1) tmp]];
    
    % concatenate y measurements of bin
    Y = [Y; y0];
end

clear x0 y0 x y tmp ind;

% Y = Y(1:head);
% obtain least-squares Y estimation
warning off;
yf = A\Y;
clear Y A;

xf = [xf, yf];
xf = bsxfun(@plus, (xf/R), T);
yf = xf(:,2);
xf = xf(:,1);






