function verification = verify_recorded_outputs(data_root)
% Replay the supplied outputs. Add code/matlab to the MATLAB path first.
% Results are saved under generated/matlab; source data are not changed.
code_dir = fileparts(mfilename('fullpath'));
repo_root = fileparts(fileparts(code_dir));
if nargin < 1 || isempty(data_root), data_root = fullfile(repo_root,'data'); end
files = dir(fullfile(data_root,'**','sensor.mat'));
assert(numel(files)==40, 'Expected 40 sensor.mat files.');
names = strings(numel(files),1); max_KF_error = zeros(numel(files),1);
max_RLS_error = zeros(numel(files),1);
max_KF_state_error = zeros(numel(files),1);
for f = 1:numel(files)
    folder = files(f).folder;
    s = load(fullfile(folder,'sensor.mat'));
    kf = load(fullfile(folder,'raw_vs_kalman.mat'));
    rl = load(fullfile(folder,'raw_vs_rls.mat'));
    raw = load(fullfile(folder,'raw.mat'));
    copies = {s,kf,rl};
    for j = 1:numel(copies)
        c = copies{j};
        assert(isequal(raw.t(:),c.t(:)) && isequal(raw.T_raw(:),c.T_raw(:)));
    end
    Ts = s.Ts;
    assert(abs(Ts-0.001)<1e-10 && all(abs(diff(s.t(:))-Ts)<1e-10));
    N = numel(s.t); yk = zeros(N,1); yr = zeros(N,1); xk = zeros(3,N);
    for k = 1:N
        z = [s.omega_u_meas(k);s.omega_r_meas(k);s.T_raw(k)];
        u = [s.tau_u(k);s.tau_r(k)];
        [yk(k),xk(:,k)] = KalmanFilterFunction(z,u,1.79,k==1,Ts);
        yr(k) = RecursiveLeastSquaresFunction(0,100,0.001,s.T_raw(k),1,0.98,k==1);
    end
    [parent,test_name] = fileparts(folder);
    [~,group_name] = fileparts(parent);
    names(f) = string(group_name) + "/" + string(test_name);
    max_KF_error(f) = max(abs(yk-kf.T_kalman(:)));
    max_RLS_error(f) = max(abs(yr-rl.T_rls(:)));
    difference = abs(xk-kf.x_hat_kalman);
    max_KF_state_error(f) = max(difference(:));
end
verification = table(names,max_KF_error,max_RLS_error,max_KF_state_error);
disp(verification);
assert(all(max_KF_error<1e-10) && all(max_RLS_error<1e-10) && all(max_KF_state_error<1e-10), ...
    'At least one replay differs from the stored output by more than 1e-10.');
outdir = fullfile(repo_root,'generated','matlab');
if ~isfolder(outdir), mkdir(outdir); end
writetable(verification,fullfile(outdir,'verification.csv'));
end
