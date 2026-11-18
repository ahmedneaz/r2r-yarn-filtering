function estimate = RecursiveLeastSquaresFunction(x0, P0, R, measurementValue, C, lambda, reset_flag)
% Verified scalar RLS recursion. Nominal settings: 0,100,0.001,z,1,0.98,true/false.
    if nargin < 1 || isempty(x0), x0 = 0; end
    if nargin < 2 || isempty(P0), P0 = 100; end
    if nargin < 3 || isempty(R), R = 0.001; end
    if nargin < 5 || isempty(C), C = 1; end
    if nargin < 6 || isempty(lambda), lambda = 0.98; end
    if nargin < 7 || isempty(reset_flag), reset_flag = false; end
    persistent x_est P_est
    if isempty(x_est) || reset_flag
        x_est = x0; P_est = P0;
    end
    Lmatrix = R + C*P_est*C';
    gainMatrix = (P_est*C')/Lmatrix;
    err = measurementValue - C*x_est;
    x_est = x_est + gainMatrix*err;
    ImKc = eye(size(x0,1)) - gainMatrix*C;
    P_est = (1/lambda)*ImKc*P_est;
    estimate = x_est;
end
