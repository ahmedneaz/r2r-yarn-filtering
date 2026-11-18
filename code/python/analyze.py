"""Reproduce the R2R comparison and offline checks from the accompanying recordings.

Usage: python analyze.py DATA_DIRECTORY_OR_ZIP --out generated/results
The supplied environment was tested with Python 3.12. No input files are modified.
Recorded online outputs are the primary comparison. Additional filters and
parameter changes are explicitly offline replays. Segments are not assumed
to be independent experimental replicates; no population p-values are computed.
"""
import argparse, csv, hashlib, io, json, platform, re, zipfile
from pathlib import Path
import numpy as np
import scipy
from scipy.io import loadmat
from scipy.signal import butter, sosfilt, sosfilt_zi, sosfiltfilt, welch, correlate, correlation_lags, lfilter

FS=1000.
BANDS=[(.5,5),(5,50),(50,450)]
SHARE_BANDS=[(0,.5),(.5,5),(5,50),(50,450),(450,500)]
JU,BU,JR,BR,RU,RR=.00793,.0101,.0043367,.010292,.04,.05
def psd(x):
    return welch(x,fs=FS,window='hann',nperseg=4096,noverlap=2048,detrend='constant',scaling='density',axis=-1)
def integral(f,p,lo,hi,interp=False):
    ix=(f>=lo)&(f<=hi)
    if not interp:return np.trapezoid(p[...,ix],f[ix],axis=-1)
    ix=(f>lo)&(f<hi);ff=np.r_[lo,f[ix],hi]
    return np.trapezoid(np.r_[np.interp(lo,f,p),p[ix],np.interp(hi,f,p)],ff)
def smooth(x,fc):return sosfiltfilt(butter(4,fc,fs=FS,output='sos'),x,axis=-1)
def metrics(raw,y):
    f,p=psd(np.stack([raw,y]));power=np.array([integral(f,p,*b) for b in BANDS]).T
    att=10*np.log10(power[0]/power[1]);sm=smooth(np.stack([raw,y]),5)
    c=correlate(sm[1]-sm[1].mean(),sm[0]-sm[0].mean(),mode='full',method='fft')
    lag=correlation_lags(len(y),len(raw),mode='full');ix=np.abs(lag)<=250
    return dict(low_db=float(att[0]),mid_db=float(att[1]),high_db=float(att[2]),
      trend_rmse_n=float(np.sqrt(np.mean((sm[1]-sm[0])**2))),trend_r=float(np.corrcoef(sm)[0,1]),
      lag_ms=float(lag[ix][np.argmax(c[ix])]),raw_high_rms_n=float(np.sqrt(power[0,2])),output_high_rms_n=float(np.sqrt(power[1,2])))
def rls(raw,lam=.98,p0=100.,r=.001,x0=0.):
    y=np.empty_like(raw);p=p0;x=x0
    for k,z in enumerate(raw):
        g=p/(r+p);x=x+g*(z-x);p=(1/lam)*(1-g)*p;y[k]=x
    return y
def scalar_lms(raw,mu):
    # C=1; minimizes 0.5*(raw-estimate)^2, x0=0; fully causal.
    return lfilter([mu],[1.,-(1-mu)],raw)
GAIN_CACHE={}
def kalman(s,kmodel=1.79):
    ts=float(s['Ts']);z=np.column_stack([s['omega_u_meas'],s['omega_r_meas'],s['T_raw']])
    u=np.column_stack([s['tau_u'],s['tau_r']]);n=len(z);key=(ts,kmodel,n)
    a=np.array([[-BU/JU,0,-RU/JU],[0,-BR/JR,RR/JR],[-kmodel*RU,kmodel*RR,0.]])
    b=np.array([[1/JU,0],[0,1/JR],[0,0.]])
    f=np.eye(3)+a*ts;bd=b*ts;qd=np.diag([10.,10.,.05])*ts;rd=np.diag([1e-4,1e-4,.015])/ts
    if key not in GAIN_CACHE:
        p=np.diag([1e-3,1e-3,1e-2]);gg=np.empty((n,3,3))
        for i in range(n):
            pm=f@p@f.T+qd;k=np.linalg.solve((pm+rd).T,pm.T).T
            p=(np.eye(3)-k)@pm;p=.5*(p+p.T);gg[i]=k
        GAIN_CACHE[key]=gg
    gg=GAIN_CACHE[key];x=z[0].copy();out=np.empty_like(z)
    for i in range(n):
        xp=f@x+bd@u[i];x=xp+gg[i]@(z[i]-xp);out[i]=x
    return out
def writecsv(path,rows):
    with open(path,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def stats(rows,keys):
    return {k:dict(zip(['q25','median','q75','min','max'],map(float,np.r_[np.percentile([r[k] for r in rows],[25,50,75]),min(r[k] for r in rows),max(r[k] for r in rows)]))) for k in keys}
def load_records(source):
    """Read the 40 supplied segments from an extracted directory or a ZIP.

    Only the input adapter was changed for the repository layout. The numerical
    calculations below are the same as in the supplementary analysis package.
    """
    source = Path(source)
    archive = None
    if source.is_dir():
        names = [p.relative_to(source).as_posix() for p in source.rglob('raw.mat')]
        read_bytes = lambda name: (source / name).read_bytes()
    elif source.is_file() and zipfile.is_zipfile(source):
        archive = zipfile.ZipFile(source)
        names = [n for n in archive.namelist() if n.endswith('/raw.mat')]
        read_bytes = archive.read
    else:
        raise FileNotFoundError(f'Expected an extracted data directory or ZIP: {source}')
    try:
        indexed = []
        for name in names:
            parts = Path(name).parts
            if len(parts) < 3 or parts[-3] not in ('Hard_Yarn_Data', 'Soft_Yarn_Data'):
                raise ValueError(f'Unrecognized data path: {name}')
            match = re.fullmatch(r'Test_(\d+)', parts[-2])
            if not match:
                raise ValueError(f'Unrecognized test folder: {name}')
            indexed.append((parts[-3], int(match[1]), name))
        expected = {(g, i) for g in ('Hard_Yarn_Data', 'Soft_Yarn_Data') for i in range(1, 21)}
        if len(indexed) != 40 or {(g, i) for g, i, _ in indexed} != expected:
            raise ValueError('Expected Test_1 through Test_20 in each of the two yarn folders.')
        for group, test, name in sorted(indexed):
            base = str(Path(name).parent).replace('\\', '/')
            arrays = [loadmat(io.BytesIO(read_bytes(base + '/' + fn)), simplify_cells=True)
                      for fn in ('raw.mat', 'sensor.mat', 'raw_vs_kalman.mat', 'raw_vs_rls.mat')]
            label = 'Lower stiffness' if group == 'Soft_Yarn_Data' else 'Higher stiffness'
            yield label, test, arrays, hashlib.sha256(read_bytes(name)).hexdigest()
    finally:
        if archive is not None:
            archive.close()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('archive');ap.add_argument('--out',default='results');args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    primary=[];powerrows=[];cutoffs=[];equal=[];baselines=[];sensitivity=[];initialization=[];matched=[];manifest=[]
    for g,test,(d,s,kf,rl),digest in load_records(args.archive):
        t=d['t'];raw=d['T_raw'];ys={'RLS':rl['T_rls'],'KF':kf['T_kalman']};ix=t>=1;meta={'yarn':g,'test':test}
        assert np.all(np.isfinite(np.column_stack([t,raw,*ys.values(),s['omega_u_meas'],s['omega_r_meas'],s['tau_u'],s['tau_r']]))),meta
        assert all(np.array_equal(t,x['t']) and np.array_equal(raw,x['T_raw']) for x in [s,kf,rl]),meta
        assert np.allclose(np.diff(t),.001,rtol=0,atol=1e-10),meta
        yr=rls(raw);yk=kalman(s)
        manifest.append(dict(meta,samples=len(t),duration_s=float(t[-1]-t[0]),sha256_raw_mat=digest,rls_max_abs_error=float(np.max(np.abs(yr-ys['RLS']))),kf_max_abs_error=float(np.max(np.abs(yk[:,2]-ys['KF']))),kf_state_max_abs_error=float(np.max(np.abs(yk.T-kf['x_hat_kalman'])))))
        for method,y in ys.items():
            primary.append(dict(meta,filter=method,**metrics(raw[ix],y[ix])))
            ie=(t>=1)&(t<=15);equal.append(dict(meta,filter=method,**metrics(raw[ie],y[ie])))
        f,p=psd(raw[ix]);den=integral(f,p,0,500,True)
        for lo,hi in SHARE_BANDS:
            pp=integral(f,p,lo,hi,True);powerrows.append(dict(meta,band=f'{lo:g}-{hi:g}',power_n2=float(pp),share_pct=float(100*pp/den)))
        for fc in [1,2,5,10]:
            sm=smooth(np.stack([raw[ix],ys['RLS'][ix],ys['KF'][ix]]),fc)
            for edge in [0,1]:
                ss=sm[:,1000:-1000] if edge else sm;rm=np.sqrt(np.mean((ss[1:]-ss[0])**2,axis=-1))
                cutoffs.append(dict(meta,cutoff_hz=fc,edge_trim_s=edge,rls_rmse_n=float(rm[0]),kf_rmse_n=float(rm[1]),paired_difference_n=float(rm[0]-rm[1])))
        for fc in [2,5,10,20]:
            sos=butter(4,fc,fs=FS,output='sos');y,_=sosfilt(sos,raw,zi=sosfilt_zi(sos)*raw[0]);baselines.append(dict(meta,filter=f'Butterworth4_{fc}Hz',**metrics(raw[ix],y[ix])))
        for mu in [.005,.01,.02,.05]:
            y=scalar_lms(raw,mu);baselines.append(dict(meta,filter=f'LMS_C1_mu{mu:g}',**metrics(raw[ix],y[ix]),max_difference_from_RLS_after_1s=float(np.max(np.abs(y[ix]-ys['RLS'][ix])))))
        for lam in [.90,.95,.98,.99,.995]:
            y=rls(raw,lam=lam);sensitivity.append(dict(meta,lambda_value=lam,**metrics(raw[ix],y[ix])))
        for name,kw in [('P0_0.001',{'p0':.001}),('P0_1',{'p0':1.}),('P0_100',{}),('P0_10000',{'p0':1e4}),('R_0.0001',{'r':.0001}),('R_0.01',{'r':.01}),('x0_minus0.2',{'x0':-.2}),('x0_plus0.2',{'x0':.2})]:
            y=rls(raw,**kw);initialization.append(dict(meta,setting=name,max_difference_startup_n=float(np.max(np.abs(y[~ix]-yr[~ix]))),max_difference_after_1s_n=float(np.max(np.abs(y[ix]-yr[ix])))))
        if g=='Lower stiffness':
            y=kalman(s,kmodel=.37)[:,2];matched.append(dict(meta,filter='KF_k0.37_offline',**metrics(raw[ix],y[ix])))
        print(f'Analyzed {g} Test {test}',flush=True)
    # CSV columns are the union, so the baseline-only diagnostic can be blank elsewhere.
    for r in baselines:r.setdefault('max_difference_from_RLS_after_1s',None)
    datasets=dict(primary_metrics=primary,raw_band_power=powerrows,cutoff_sensitivity=cutoffs,equal_duration_metrics=equal,baseline_metrics=baselines,rls_sensitivity=sensitivity,initialization_sensitivity=initialization,kf_stiffness_replay=matched,record_manifest=manifest)
    for name,rows in datasets.items():writecsv(out/(name+'.csv'),rows)
    keys=['low_db','mid_db','high_db','trend_rmse_n','trend_r','lag_ms','raw_high_rms_n','output_high_rms_n'];summary={'versions':dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),'groups':{}}
    for g in ['Higher stiffness','Lower stiffness']:
        gg={}
        for name,rows in [('primary',primary),('equal_duration',equal),('baselines',baselines),('kf_stiffness_replay',matched)]:
            rr=[r for r in rows if r['yarn']==g];gg[name]={m:stats([r for r in rr if r['filter']==m],keys) for m in sorted({r['filter'] for r in rr})}
        gg['raw_power']={band:stats([r for r in powerrows if r['yarn']==g and r['band']==band],['power_n2','share_pct']) for band in [f'{lo:g}-{hi:g}' for lo,hi in SHARE_BANDS]}
        gg['rls_sensitivity']={str(lam):stats([r for r in sensitivity if r['yarn']==g and r['lambda_value']==lam],keys) for lam in [.90,.95,.98,.99,.995]}
        gg['cutoff_sensitivity']={f'{fc}_{edge}':dict(stats([r for r in cutoffs if r['yarn']==g and r['cutoff_hz']==fc and r['edge_trim_s']==edge],['rls_rmse_n','kf_rmse_n','paired_difference_n']),rls_lower_count=sum(r['paired_difference_n']<0 for r in cutoffs if r['yarn']==g and r['cutoff_hz']==fc and r['edge_trim_s']==edge)) for fc in [1,2,5,10] for edge in [0,1]}
        pp=[r for r in primary if r['yarn']==g];diff=[next(r['high_db'] for r in pp if r['test']==i and r['filter']=='RLS')-next(r['high_db'] for r in pp if r['test']==i and r['filter']=='KF') for i in range(1,21)]
        gg['paired_high_difference']=dict(zip(['q25','median','q75'],map(float,np.percentile(diff,[25,50,75]))));gg['rls_higher_attenuation_count']=sum(v>0 for v in diff);gg['representative_test']=int(np.argmin(np.abs(np.array(diff)-np.median(diff)))+1)
        gg['initialization_max_after_1s']=max(r['max_difference_after_1s_n'] for r in initialization if r['yarn']==g)
        summary['groups'][g]=gg
    summary['verification']={'rls_max_abs':max(r['rls_max_abs_error'] for r in manifest),'kf_max_abs':max(r['kf_max_abs_error'] for r in manifest)}
    summary['complexity']={'sample_count_example':15001,'RLS_C1_per_sample':{'multiply':2,'add_subtract':4,'divide':2,'persistent_scalars':2},'KF_HI_dense_per_sample':{'multiply':114,'add_subtract':114,'matrix_right_solve_3x3':1,'persistent_scalars':12},'scope':'Algebraic operation counts; excludes initialization, matrix construction, indexing, and the arithmetic internal to the 3x3 solve. Not measured execution time.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print('Saved analysis to',out)
if __name__=='__main__':main()
