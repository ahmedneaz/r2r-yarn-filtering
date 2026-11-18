function fig = plot_recorded_segment(yarn_group, test_number)
% View one unshifted segment without extra filtering.
% Example: plot_recorded_segment('Soft_Yarn_Data',1)
    if nargin < 1, yarn_group = 'Soft_Yarn_Data'; end
    if nargin < 2, test_number = 1; end
    validatestring(yarn_group,{'Hard_Yarn_Data','Soft_Yarn_Data'});
    validateattributes(test_number,{'numeric'},{'scalar','integer','>=',1,'<=',20});
    repo_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    folder = fullfile(repo_root,'data',yarn_group,sprintf('Test_%d',test_number));
    raw = load(fullfile(folder,'raw.mat'));
    kf = load(fullfile(folder,'raw_vs_kalman.mat'));
    rl = load(fullfile(folder,'raw_vs_rls.mat'));
    assert(isequal(raw.t(:),kf.t(:)) && isequal(raw.t(:),rl.t(:)));
    fig = figure('Color','white');
    plot(raw.t,raw.T_raw,'Color',[.45 .45 .45]); hold on;
    plot(kf.t,kf.T_kalman,'Color',[.77 .31 .19]);
    plot(rl.t,rl.T_rls,'Color',[.07 .39 .61]);
    grid on;
    xlabel('Time (s)','FontName','Times New Roman');
    ylabel('Tension (N)','FontName','Times New Roman');
    title(sprintf('%s, Test %d',yarn_group,test_number),'Interpreter','none','FontName','Times New Roman');
    legend('Recorded tension','KF','RLS','FontName','Times New Roman','Location','best');
    set(gca,'FontName','Times New Roman');
end
