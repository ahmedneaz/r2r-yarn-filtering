"""Generate journal figures with genuine Times New Roman installed locally.
Usage: python make_figures.py DATA_DIRECTORY_OR_ZIP --results generated/results --out generated/figures
"""
import argparse,json,csv,os
from pathlib import Path
import numpy as np
import matplotlib as mpl
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from analyze import load_records,psd

def fonts():
    # Standard system installations are discovered by Matplotlib. An optional
    # directory supports licensed local font copies without bundling font files.
    font_dir = os.environ.get('R2R_FONT_DIR')
    if font_dir:
        for p in Path(font_dir).rglob('*'):
            if p.suffix.lower() in ('.ttf', '.otf'):
                font_manager.fontManager.addfont(str(p))
    try:
        font_manager.findfont(font_manager.FontProperties(family='Times New Roman'),fallback_to_default=False)
    except ValueError as exc:
        raise RuntimeError('Times New Roman is required for journal figures. Install it locally or set R2R_FONT_DIR to a directory containing your licensed fonts. The numerical analysis does not require this font.') from exc
    mpl.rcParams.update({'font.family':'Times New Roman','font.cursive':['Times New Roman'],'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'legend.fontsize':9,'pdf.fonttype':42,'ps.fonttype':42,'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold','mathtext.fallback':None,'axes.spines.top':False,'axes.spines.right':False})
BLUE='#12649B';RED='#C55030';GRAY='#777777';GREEN='#23794D'
def save(fig,out,name):
    fig.savefig(out/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white');fig.savefig(out/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close(fig)
def box(ax,x,y,w,h,text,color='white',fontsize=10):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06,rounding_size=0.08',facecolor=color,edgecolor='#777777',linewidth=.8));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fontsize)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,linewidth=.9,color='#444444',connectionstyle='arc3'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('archive');ap.add_argument('--results',default='results');ap.add_argument('--out',default='figures');a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);fonts()
    s=json.loads((Path(a.results)/'summary.json').read_text());records=list(load_records(a.archive))
    fig,ax=plt.subplots(figsize=(7.25,3.8));ax.set(xlim=(0,10.7),ylim=(0,6));ax.axis('off')
    ax.text(5.35,5.72,'Tune both filters on the higher-stiffness yarn',ha='center',fontsize=12,fontweight='bold')
    ax.text(5.35,5.3,'Retain the same settings for the lower-stiffness yarn',ha='center',fontsize=10)
    box(ax,.15,3.8,2.35,.8,'Load-cell tension\nT raw')
    box(ax,.15,2.25,2.35,.8,'Encoder speeds\nboth rollers')
    box(ax,.15,.7,2.35,.8,'Motor-driver torques\nboth rollers')
    box(ax,4,3.8,2.5,.8,'Scalar RLS\nC = 1, lambda = 0.98','#EEF5FA')
    box(ax,4,1.25,2.5,1.15,'Three-state KF\nTwo speeds + tension\nk model = 1.79 N/m','#FAF0EC',9.5)
    box(ax,8,2.2,2.4,1.55,'Paired analysis\nBand power\nTrend similarity\nRelative lag',fontsize=10)
    arrow(ax,(2.56,4.2),(3.94,4.2));arrow(ax,(2.56,3.95),(3.94,2.3));arrow(ax,(2.56,2.65),(3.94,2));arrow(ax,(2.56,1.1),(3.94,1.6));arrow(ax,(6.56,4.2),(7.94,3.5));arrow(ax,(6.56,1.8),(7.94,2.5))
    ax.text(5.35,.18,'Online physical operation at 1 kHz; recorded segments are not independent experimental trials.',ha='center',fontsize=9)
    save(fig,out,'figure_2_design')
    fig,ax=plt.subplots(figsize=(7.25,4.4));ax.set(xlim=(0,10.5),ylim=(0,8));ax.axis('off')
    ax.text(2.5,7.65,'Kalman filter',ha='center',fontsize=13,fontweight='bold');ax.text(8,7.65,'Scalar RLS',ha='center',fontsize=13,fontweight='bold')
    left=['Read encoder speeds, tension\nand motor-driver torques','Predict state and covariance\nx predicted = F x previous + Bd u','Compute innovation and Kalman gain\nK = P predicted / (P predicted + Rd)','Correct state and covariance\nx = x predicted + K (z - x predicted)','Return the tension state and retain x, P']
    right=['Read the current load-cell tension','Compute the scalar gain\ng = P / (R + P)','Update the tension estimate\nT = T previous + g (T raw - T previous)','Update uncertainty with forgetting\nP = (1 - g) P / lambda','Return the estimate; retain T, P']
    for j,(l,r) in enumerate(zip(left,right)):
        y=6.25-j*1.25;box(ax,.15,y,4.7,.82,l,'#FAF0EC' if j in [1,3] else 'white',9.5);box(ax,5.65,y,4.7,.82,r,'#EEF5FA' if j in [1,3] else 'white',9.5)
        if j<4:arrow(ax,(2.5,y-.06),(2.5,y-.4));arrow(ax,(8,y-.06),(8,y-.4))
    ax.text(2.5,.25,'Uses the mechanical model and uncertainty tuning',ha='center',fontsize=9)
    ax.text(8,.25,'At steady state, g approaches 0.02',ha='center',fontsize=9)
    save(fig,out,'figure_3_algorithms')
    fig,axs=plt.subplots(2,1,figsize=(7.25,4.1),constrained_layout=True)
    for ax,g in zip(axs,['Higher stiffness','Lower stiffness']):
        test=s['groups'][g]['representative_test'];_,_,(d,sen,kf,rl),_=next(r for r in records if r[0]==g and r[1]==test);ix=d['t']<=8
        for y,col,label,lw in [(d['T_raw'],GRAY,'Recorded tension',.8),(kf['T_kalman'],RED,'KF',1.1),(rl['T_rls'],BLUE,'RLS',1.1)]:ax.plot(d['t'][ix],y[ix],color=col,label=label,lw=lw)
        ax.set_title(f'{g}: Test {test}',loc='left');ax.set_ylabel('Tension (N)');ax.grid(alpha=.18);ax.margins(x=0)
    axs[0].legend(loc='best',ncol=3);axs[-1].set_xlabel('Time (s)');save(fig,out,'figure_4_traces')
    fig,axs=plt.subplots(1,2,figsize=(7.25,3.2),sharey=True,constrained_layout=True)
    for ax,g in zip(axs,['Higher stiffness','Lower stiffness']):
        for method,dx,col in [('RLS',-.13,BLUE),('KF',.13,RED)]:
            vv=s['groups'][g]['primary'][method];vals=[vv[k] for k in ['low_db','mid_db','high_db']];med=np.array([v['median'] for v in vals]);err=np.array([[v['median']-v['q25'] for v in vals],[v['q75']-v['median'] for v in vals]])
            ax.errorbar(np.arange(3)+dx,med,yerr=err,fmt='o',color=col,capsize=4,label=method)
        ax.axhline(0,color=GRAY,lw=.7);ax.set_xticks(range(3),['0.5–5','5–50','50–450']);ax.set_xlabel('Frequency band (Hz)');ax.set_title(g);ax.grid(axis='y',alpha=.18)
    axs[0].set_ylabel('Attenuation (dB)');axs[1].legend();save(fig,out,'figure_5_attenuation')
    met=list(csv.DictReader(open(Path(a.results)/'primary_metrics.csv')));manifest=list(csv.DictReader(open(Path(a.results)/'record_manifest.csv')))
    fig,axs=plt.subplots(1,2,figsize=(7.25,3.1),sharey=True,constrained_layout=True)
    markers={15:'o',20:'s',30:'^'}
    for ax,g in zip(axs,['Higher stiffness','Lower stiffness']):
        for t in range(1,21):
            rr=[r for r in met if r['yarn']==g and int(r['test'])==t];dd={r['filter']:float(r['high_db']) for r in rr};dur=int(float(next(r['duration_s'] for r in manifest if r['yarn']==g and int(r['test'])==t)))
            ax.scatter(t,dd['RLS']-dd['KF'],marker=markers[dur],s=30,color=BLUE)
        ax.axhline(s['groups'][g]['paired_high_difference']['median'],color=GRAY,ls='--',lw=.8);ax.axhline(0,color='black',lw=.7);ax.set_title(g);ax.set_xlabel('Test segment');ax.set_xticks([1,5,10,15,20]);ax.grid(alpha=.15)
    axs[0].set_ylabel('RLS minus KF attenuation (dB)');axs[0].set_ylim(bottom=-1)
    for dur,mark in markers.items():axs[1].scatter([],[],marker=mark,color=BLUE,label=f'{dur} s')
    axs[1].legend(ncol=3,loc='lower right',fontsize=8);save(fig,out,'figure_6_paired')
    fig,axs=plt.subplots(1,2,figsize=(7.25,3.3),sharey=True,constrained_layout=True)
    for ax,g in zip(axs,['Higher stiffness','Lower stiffness']):
        pp={'Recorded tension':[],'RLS':[],'KF':[]}
        for gg,t,(d,sen,kf,rl),_ in records:
            if gg!=g:continue
            ix=d['t']>=1
            for label,y in [('Recorded tension',d['T_raw']),('RLS',rl['T_rls']),('KF',kf['T_kalman'])]:f,p=psd(y[ix]);pp[label].append(p)
        for label,col in [('Recorded tension',GRAY),('RLS',BLUE),('KF',RED)]:ax.loglog(f[1:],np.median(pp[label],axis=0)[1:],label=label,color=col,lw=1)
        for boundary in [5,50,450]:ax.axvline(boundary,color='#CCCCCC',lw=.6)
        ax.set_title(g);ax.set_xlabel('Frequency (Hz)');ax.grid(alpha=.15)
    axs[0].set_ylabel('PSD (N²/Hz)');axs[1].legend(fontsize=8);save(fig,out,'figure_S1_psd')
    fig,axs=plt.subplots(1,2,figsize=(7.25,3.4),sharey=True,constrained_layout=True)
    for ax,g in zip(axs,['Higher stiffness','Lower stiffness']):
        q=s['groups'][g];vals=[q['rls_sensitivity'][str(l)] for l in [.90,.95,.98,.99,.995]]
        ax.plot([v['trend_rmse_n']['median'] for v in vals],[v['high_db']['median'] for v in vals],'-o',color=BLUE,label='RLS forgetting-factor sweep')
        for lam,v in zip([.90,.95,.98,.99,.995],vals):ax.annotate(str(lam),(v['trend_rmse_n']['median'],v['high_db']['median']),xytext=(3,5) if lam==.9 else (3,-12),textcoords='offset points',fontsize=8)
        bb=[q['baselines'][f'Butterworth4_{fc}Hz'] for fc in [2,5,10,20]]
        ax.plot([v['trend_rmse_n']['median'] for v in bb],[v['high_db']['median'] for v in bb],'-s',color=GREEN,label='Causal fourth-order Butterworth')
        for fc,v in zip([2,5,10,20],bb):ax.annotate(f'{fc} Hz',(v['trend_rmse_n']['median'],v['high_db']['median']),xytext=(3,4),textcoords='offset points',fontsize=8)
        ax.set_title(g);ax.set_xlabel('Median trend-proxy deviation (N)');ax.grid(alpha=.15)
    axs[0].set_ylabel('Median 50–450 Hz attenuation (dB)');axs[0].legend(fontsize=7.5,loc='lower right');save(fig,out,'figure_S2_tradeoff')
    print('Generated Times New Roman figures in',out)
if __name__=='__main__':main()
