function [T_est, x_hat] = KalmanFilterFunction(z, u, k_model, reset_flag, Ts)
% Verified three-state Forward Euler KF for the accompanying recordings.
% z = [omega_u_meas; omega_r_meas; T_raw]; u = [tau_u; tau_r].
% Torque channels are reported values from the two motor drivers.
    if nargin < 3 || isempty(k_model), k_model = 1.79; end
    if nargin < 4 || isempty(reset_flag), reset_flag = false; end
    if nargin < 5 || isempty(Ts), Ts = 0.001; end
    Ju = 7.93e-3; Bu = 1.01e-2;
    Jr = 4.3367e-3; Br = 1.0292e-2;
    ru = 0.04; rr = 0.05;
    A = [-Bu/Ju, 0, -ru/Ju;
         0, -Br/Jr, rr/Jr;
         -k_model*ru, k_model*rr, 0];
    B = [1/Ju, 0; 0, 1/Jr; 0, 0];
    I3 = eye(3); F = I3 + A*Ts; Bd = B*Ts;
    H = eye(3);
    Qc = diag([10.0, 10.0, 0.05]);
    Rc = diag([1e-4, 1e-4, 0.015]);
    % First-order process covariance and continuous-intensity measurement scaling.
    Qd = Qc*Ts; Rd = Rc/Ts;
    persistent x_prev P_prev
    if isempty(x_prev) || reset_flag
        x_prev = [z(1); z(2); z(3)];
        P_prev = diag([1e-3, 1e-3, 1e-2]);
    end
    x_pred = F*x_prev + Bd*u(:);
    P_pred = F*P_prev*F' + Qd;
    S = H*P_pred*H' + Rd;
    K = (P_pred*H')/S;
    x_curr = x_pred + K*(z(:) - H*x_pred);
    P_curr = (I3 - K*H)*P_pred;
    P_curr = 0.5*(P_curr + P_curr');
    x_prev = x_curr; P_prev = P_curr;
    x_hat = x_curr; T_est = x_curr(3);
end
