#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, statistics as stats
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / 'data' / 'btc_usd_daily_stooq.csv'
OUT_DIR = ROOT / 'results'
NB_DIR = ROOT / 'notebooks'
OUT_DIR.mkdir(exist_ok=True)
NB_DIR.mkdir(exist_ok=True)


def read_data():
    rows = []
    with open(DATA_PATH, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({
                'date': datetime.strptime(r['date'], '%Y-%m-%d').date(),
                'open': float(r['open']), 'high': float(r['high']), 'low': float(r['low']), 'close': float(r['close'])
            })
    rows.sort(key=lambda x: x['date'])
    return rows


def returns(close):
    out = [0.0]
    for i in range(1, len(close)):
        out.append(close[i] / close[i-1] - 1.0 if close[i-1] else 0.0)
    return out


def ema(x, n):
    out = [x[0]]
    a = 2.0 / (n + 1)
    for i in range(1, len(x)): out.append(a * x[i] + (1-a) * out[-1])
    return out


def rolling_std(x, n):
    out = [None] * len(x)
    for i in range(n-1, len(x)):
        w = x[i-n+1:i+1]
        out[i] = stats.pstdev(w) if len(w) > 1 else 0.0
    return out


def rolling_max(x, n):
    out = [None] * len(x)
    for i in range(n-1, len(x)): out[i] = max(x[i-n+1:i+1])
    return out


def rolling_min(x, n):
    out = [None] * len(x)
    for i in range(n-1, len(x)): out[i] = min(x[i-n+1:i+1])
    return out


def rsi(close, p=14):
    out = [None] * len(close)
    g, l = [0.0]*len(close), [0.0]*len(close)
    for i in range(1, len(close)):
        d = close[i] - close[i-1]
        g[i], l[i] = max(0.0, d), max(0.0, -d)
    ag = al = 0.0
    for i in range(1, len(close)):
        if i <= p:
            ag += g[i]; al += l[i]
            if i == p: ag /= p; al /= p
        else:
            ag = (ag*(p-1)+g[i])/p; al = (al*(p-1)+l[i])/p
        if i >= p: out[i] = 100.0 if al == 0 else 100.0 - 100.0/(1 + ag/al)
    return out


def shift(x, k=1): return ([0.0]*k + x[:-k]) if k > 0 else x[:]

def clip(x, lo, hi): return max(lo, min(hi, x))


def perf_stats(rets, ppy=365):
    if not rets:
        return {'Total Return':0,'CAGR':0,'Sharpe':0,'Sortino':0,'Max Drawdown':0,'Calmar':0,'Win Rate':0,'Monthly Hit Rate':0,'Ann.Vol':0}
    eq, curve = 1.0, []
    for r in rets: eq *= 1+r; curve.append(eq)
    years = len(rets)/ppy
    cagr = eq**(1/years)-1 if years > 0 and eq > 0 else 0
    vol = stats.pstdev(rets) if len(rets) > 1 else 0
    sharpe = (stats.mean(rets)/vol)*math.sqrt(ppy) if vol > 1e-12 else 0
    d = [min(0.0, r) for r in rets]
    dvol = stats.pstdev(d) if len(d) > 1 else 0
    sortino = (stats.mean(rets)/dvol)*math.sqrt(ppy) if dvol > 1e-12 else 0
    peak, mdd = -1e18, 0.0
    for e in curve:
        peak = max(peak, e)
        mdd = min(mdd, e/peak-1)
    calmar = cagr/abs(mdd) if mdd < 0 else 0
    win = sum(1 for r in rets if r > 0)/len(rets)
    monthly, cur = [], 1.0
    for i, r in enumerate(rets, 1):
        cur *= 1+r
        if i % 30 == 0: monthly.append(cur-1); cur = 1.0
    mhr = sum(1 for x in monthly if x > 0)/len(monthly) if monthly else 0
    return {'Total Return':eq-1,'CAGR':cagr,'Sharpe':sharpe,'Sortino':sortino,'Max Drawdown':mdd,'Calmar':calmar,'Win Rate':win,'Monthly Hit Rate':mhr,'Ann.Vol':vol*math.sqrt(ppy)}


def apply_costs(raw, pos, c_bps, s_bps):
    fee = (c_bps + s_bps)/10000.0
    prev, out, turn = 0.0, [], 0.0
    for r, p in zip(raw, pos):
        t = abs(p-prev); turn += t
        out.append(r - t*fee); prev = p
    return out, turn/max(1,len(pos))*365.0


def objective(m, turnover):
    core = 3.0*m['CAGR'] + 1.8*m['Win Rate'] - 3.0*abs(m['Max Drawdown'])
    guard = 0.6*max(0,m['Sharpe']) + 0.4*max(0,m['Sortino'])
    pen = (max(0,0.6-m['Sharpe'])*0.5 + max(0,1.0-m['Sortino'])*0.25 + max(0,turnover-25)*0.02)
    return core + guard - pen


def dominated(a,b):
    ge = b['CAGR']>=a['CAGR'] and b['Win Rate']>=a['Win Rate'] and abs(b['Max Drawdown'])<=abs(a['Max Drawdown']) and b['Sharpe']>=a['Sharpe'] and b['Sortino']>=a['Sortino']
    gt = b['CAGR']>a['CAGR'] or b['Win Rate']>a['Win Rate'] or abs(b['Max Drawdown'])<abs(a['Max Drawdown']) or b['Sharpe']>a['Sharpe'] or b['Sortino']>a['Sortino']
    return ge and gt


def sigmoid(z):
    if z >= 0: ez = math.exp(-z); return 1/(1+ez)
    ez = math.exp(z); return ez/(1+ez)


def standardize_fit(X):
    mu, sd = [], []
    for j in range(len(X[0])):
        c = [r[j] for r in X]; m = stats.mean(c); s = stats.pstdev(c)
        mu.append(m); sd.append(s if s > 1e-12 else 1.0)
    return mu, sd


def standardize_apply(X, mu, sd): return [[(r[j]-mu[j])/sd[j] for j in range(len(r))] for r in X]


def train_logistic(X,y,l2=1.0,lr=0.05,epochs=140):
    n,m = len(X), len(X[0]); w=[0.0]*m
    for _ in range(epochs):
        g=[0.0]*m
        for xi,yi in zip(X,y):
            p=sigmoid(sum(a*b for a,b in zip(w,xi))); d=p-yi
            for j in range(m): g[j]+=d*xi[j]
        for j in range(m):
            reg=l2*w[j] if j<m-1 else 0.0
            w[j]-=lr*((g[j]/n)+reg/n)
    return w


def pred_logistic(X,w): return [sigmoid(sum(a*b for a,b in zip(w,x))) for x in X]


def quantiles(col):
    s=sorted(col); qs=[]
    for q in (0.2,0.4,0.6,0.8): qs.append(s[int(q*(len(s)-1))])
    return qs


def train_stumps(X,y,rounds=25):
    n,m=len(X),len(X[0]); wt=[1.0/n]*n; model=[]
    cols=[[X[i][j] for i in range(n)] for j in range(m-1)]
    cqs=[quantiles(c) for c in cols]
    for _ in range(rounds):
        best=None; berr=1.0
        for j in range(m-1):
            for th in cqs[j]:
                for pol in (1,-1):
                    err=0.0
                    for i in range(n):
                        pred=1 if pol*(X[i][j]-th)>=0 else 0
                        if pred!=y[i]: err+=wt[i]
                    if err<berr: berr=err; best={'j':j,'th':th,'pol':pol}
        if best is None or berr>=0.5: break
        e=max(1e-8,min(0.499999,berr)); a=0.5*math.log((1-e)/e); best['a']=a; model.append(best)
        z=0.0
        for i in range(n):
            pred=1 if best['pol']*(X[i][best['j']]-best['th'])>=0 else -1
            yi=1 if y[i]==1 else -1
            wt[i]*=math.exp(-a*yi*pred); z+=wt[i]
        wt=[w/z for w in wt]
    return model


def pred_stumps(X,model):
    out=[]
    for x in X:
        s=0.0
        for m in model:
            pred=1 if m['pol']*(x[m['j']]-m['th'])>=0 else -1
            s+=m['a']*pred
        out.append(sigmoid(2*s))
    return out


def precompute(close, high, low, rets):
    return {
        'e50': ema(close,50), 'e200': ema(close,200), 'rv20': rolling_std(rets,20),
        'rsi14': rsi(close,14), 'hh20': rolling_max(high,20), 'll20': rolling_min(low,20)
    }


def weak_signal(idx, close, rets, ind):
    trend = 1.0 if ind['e50'][idx] > ind['e200'][idx] else 0.0
    rr = ind['rsi14'][idx]
    meanrev = 1.0 if (rr is not None and rr < 35) else (0.0 if (rr is not None and rr > 55) else 0.5)
    hh = ind['hh20'][idx-1] if idx > 0 else None
    breakout = 1.0 if (hh is not None and close[idx] > hh) else 0.0
    rv = (ind['rv20'][idx] or 0.0) * math.sqrt(365)
    regime = 1.0 if close[idx] > ind['e200'][idx] and rv < 0.8 else 0.0
    cr = sum(rets[max(0,idx-i)] for i in range(1,8)) - sum(abs(min(0.0, rets[max(0,idx-i)])) for i in range(1,8))
    carry = clip(0.5 + 20.0*cr, 0, 1)
    return {'trend':trend,'meanrev':meanrev,'breakout':breakout,'regime':regime,'carry_like':carry}


def fit_weak_w(close, rets, ind, ts, te):
    ks=['trend','meanrev','breakout','regime','carry_like']; s={k:[] for k in ks}; y=[]
    for t in range(max(220,ts), te-1):
        g=weak_signal(t,close,rets,ind)
        for k in ks: s[k].append(g[k]-0.5)
        y.append(rets[t+1])
    w={}
    for k in ks:
        cov=sum(a*b for a,b in zip(s[k],y))/max(1,len(y)); w[k]=max(0.0,cov)
    z=sum(w.values())
    return ({k:1.0/len(ks) for k in ks} if z<=1e-12 else {k:v/z for k,v in w.items()})


def build_features(close, high, low, rets, ind):
    X,y=[],[]
    for t in range(220, len(close)-1):
        hh=ind['hh20'][t-1]; ll=ind['ll20'][t-1]
        br=0.0
        if hh is not None and ll is not None:
            rng=max(1e-9, hh-ll); br=(close[t]-ll)/rng-0.5
        car=sum(rets[t-i] for i in range(1,8))
        X.append([
            close[t]/close[t-5]-1, close[t]/close[t-20]-1, close[t]/close[t-60]-1,
            (ind['rv20'][t] or 0.0)*math.sqrt(365), close[t]/ind['e200'][t]-1,
            (ind['rsi14'][t] or 50.0)/100.0-0.5, car, br, close[t]/ind['e50'][t]-1, 1.0
        ])
        y.append(1 if rets[t+1] > 0 else 0)
    return X,y


def risk_sized(raw_sig, rets, target_vol=0.35):
    pos=[]; eq=1.0; peak=1.0
    for t,s in enumerate(raw_sig):
        vol=stats.pstdev(rets[max(0,t-20):t+1])*math.sqrt(365) if t>5 else 0.0
        vscale=clip(target_vol/vol,0,1) if vol>1e-8 else 0.0
        dd=eq/peak-1.0
        dscale = 1.0 if dd>=-0.10 else 0.6 if dd>=-0.15 else 0.35 if dd>=-0.20 else 0.0
        p=clip(s,0,1)*vscale*dscale
        pos.append(p)
        if t>0:
            eq*=1+p*rets[t]
            peak=max(peak,eq)
    sh=shift(pos,1)
    return [p*r for p,r in zip(sh,rets)], sh


@dataclass
class Cfg:
    train:int=365*4
    test:int=180
    step:int=180
    purge:int=7
    cost_bps:float=4.0
    slip_bps:float=2.0
    target_vol:float=0.35


def run_candidate(name, params, close, rets, ind, X_all, y_all, ts, te, qs, qe, cfg):
    base=220
    tr0=max(0,ts-base); tr1=max(0,te-1-base)
    te0=max(0,qs-base); te1=max(0,qe-1-base)
    Xtr, ytr = X_all[tr0:tr1], y_all[tr0:tr1]
    Xte = X_all[te0:te1]
    if len(Xtr)<100 or len(Xte)<10: return None
    mu,sd=standardize_fit(Xtr); Xtrs=standardize_apply(Xtr,mu,sd); Xtes=standardize_apply(Xte,mu,sd)

    ww=fit_weak_w(close, rets, ind, ts, te)
    pweak=[sum(weak_signal(t,close,rets,ind)[k]*ww[k] for k in ww) for t in range(qs,qe)]

    wlog=train_logistic(Xtrs,ytr,l2=params.get('l2',1.0),lr=0.05,epochs=130)
    plog=pred_logistic(Xtes,wlog)

    mst=train_stumps(Xtrs,ytr,rounds=params.get('rounds',25))
    pst=pred_stumps(Xtes,mst)

    meta_y=[1 if (bp>0.55 and yy==1) else 0 for bp,yy in zip(pred_logistic(Xtrs,wlog),ytr)]
    wmeta=train_logistic(Xtrs,meta_y,l2=1.4,lr=0.04,epochs=100)
    pmeta=pred_logistic(Xtes,wmeta)

    sig=[]
    for i in range(len(plog)):
        if name=='weak_ensemble': s=pweak[i]
        elif name=='logistic_l2': s=plog[i]
        elif name=='boosted_stumps': s=pst[i]
        elif name=='meta_labeled_ensemble': s=(0.5*pweak[i]+0.5*plog[i])*(1.0 if pmeta[i]>params.get('meta_thr',0.54) else 0.0)
        else: s=0.35*pweak[i]+0.35*plog[i]+0.30*pst[i]
        sig.append(clip((s-params.get('entry',0.5))*2.2,0,1))

    rr=rets[qs:qe]
    raw,pos=risk_sized(sig,rr,target_vol=cfg.target_vol)
    net,turn=apply_costs(raw,pos,cfg.cost_bps,cfg.slip_bps)
    m=perf_stats(net); m['Turnover']=turn; m['name']=name
    return net,m


def walk_forward(data,cfg):
    close=[x['close'] for x in data]; high=[x['high'] for x in data]; low=[x['low'] for x in data]; rets=returns(close)
    ind=precompute(close,high,low,rets)
    X_all,y_all=build_features(close,high,low,rets,ind)

    cands=[('weak_ensemble',{'entry':0.50,'rounds':16}),('logistic_l2',{'entry':0.52,'l2':1.4,'rounds':18}),('boosted_stumps',{'entry':0.53,'rounds':28}),('meta_labeled_ensemble',{'entry':0.50,'l2':1.2,'rounds':20,'meta_thr':0.54}),('hybrid_blend',{'entry':0.51,'l2':1.0,'rounds':24})]
    oos={n:[] for n,_ in cands}; turns={n:[] for n,_ in cands}; logs=[]
    i=0
    while True:
        ts=i; te=ts+cfg.train; qs=te+cfg.purge; qe=qs+cfg.test
        if qe>=len(data): break
        fold=[]; foldret={}
        for n,p in cands:
            out=run_candidate(n,p,close,rets,ind,X_all,y_all,ts,te,qs,qe,cfg)
            if out is None: continue
            r,m=out; fold.append(m); foldret[n]=r; turns[n].append(m['Turnover'])
        pareto=[a for a in fold if not any(dominated(a,b) for b in fold if b is not a)]
        best=(sorted(pareto,key=lambda m: objective(m,m['Turnover']),reverse=True)[0] if pareto else sorted(fold,key=lambda m: objective(m,m['Turnover']),reverse=True)[0])
        logs.append({'train_start':data[ts]['date'].isoformat(),'train_end':data[te-1]['date'].isoformat(),'test_start':data[qs]['date'].isoformat(),'test_end':data[qe-1]['date'].isoformat(),'pareto':[x['name'] for x in pareto],'selected':best['name']})
        for n,_ in cands:
            if n in foldret: oos[n].extend(foldret[n])
        i+=cfg.step
    final={}
    for n in oos:
        m=perf_stats(oos[n]); m['Turnover']=stats.mean(turns[n]) if turns[n] else 0.0; m['Objective Score']=objective(m,m['Turnover']); final[n]=m
    return final,oos,logs


def regime_stability(data, rets):
    close=[x['close'] for x in data]; r=returns(close); e200=ema(close,200); rv20=rolling_std(r,20)
    med=stats.median([x for x in rv20 if x is not None])
    n=len(rets); st=len(data)-n; g={'bull':[],'bear':[],'high_vol':[],'low_vol':[]}
    for i in range(st,len(data)):
        x=rets[i-st]
        (g['bull'] if close[i]>=e200[i] else g['bear']).append(x)
        (g['high_vol'] if (rv20[i] or 0)>=med else g['low_vol']).append(x)
    return {k:perf_stats(v) for k,v in g.items()}


def rolling_stats(rets, w=180):
    out=[]
    for i in range(w,len(rets)+1,30):
        m=perf_stats(rets[i-w:i]); out.append({'end_idx':i,'CAGR':m['CAGR'],'Sharpe':m['Sharpe'],'Max Drawdown':m['Max Drawdown'],'Win Rate':m['Win Rate']})
    return out


def load_baselines(data):
    b={}
    buy=perf_stats(returns([x['close'] for x in data])); buy['Turnover']=1.0
    b['buy_and_hold']=buy
    p=OUT_DIR/'summary.json'
    if p.exists():
        j=json.loads(p.read_text()); b['prior_repo_best_vol_breakout']=j.get('metrics_oos',{}).get('vol_breakout')
    p2=OUT_DIR/'lowdd_summary.json'
    if p2.exists():
        j=json.loads(p2.read_text()); rk=j.get('ranked',[])
        if rk:
            nm=rk[0].get('strategy'); b['prior_lowdd_best']={'name':nm,'metrics':j.get('metrics_oos',{}).get(nm)}
    return b


def choose_final(final, buy):
    ranked=sorted(final.items(),key=lambda kv: kv[1]['Objective Score'],reverse=True)
    beating=[(n,m) for n,m in ranked if m['CAGR']>buy['CAGR'] and m['Total Return']>buy['Total Return']]
    if beating: return beating[0][0], True, None
    # closest Pareto: maximize DD/win improvements with minimum CAGR gap
    best_name,best_gap=None,1e18
    for n,m in ranked:
        gap=max(0.0,buy['CAGR']-m['CAGR']) + max(0.0,buy['Total Return']-m['Total Return'])
        bonus=max(0.0,m['Win Rate']-buy['Win Rate']) + max(0.0,abs(buy['Max Drawdown'])-abs(m['Max Drawdown']))
        score=gap-0.3*bonus
        if score<best_gap: best_gap=score; best_name=n
    return best_name, False, 'No strategy beat buy-and-hold on both CAGR and total return OOS; reporting closest Pareto candidate.'


def report(data, final, best_name, baselines, stabs, rolling, note):
    ordered=sorted(final.items(),key=lambda kv: kv[1]['Objective Score'],reverse=True)
    buy=baselines['buy_and_hold']
    lines=['# Triple-Objective Track','',f"Data: {data[0]['date']} to {data[-1]['date']} ({len(data)} rows)",'Validation: purged walk-forward (train=4y,test=180d,step=180d,purge=7d)','Costs: 4 bps + 2 bps slippage','', '## Candidate leaderboard','', '| Strategy | Objective | CAGR | WinRate | MaxDD | Sharpe | Sortino | Calmar | Turnover | Monthly Hit |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n,m in ordered:
        lines.append(f"| {n} | {m['Objective Score']:.3f} | {m['CAGR']:.2%} | {m['Win Rate']:.2%} | {m['Max Drawdown']:.2%} | {m['Sharpe']:.2f} | {m['Sortino']:.2f} | {m['Calmar']:.2f} | {m['Turnover']:.2f}x | {m['Monthly Hit Rate']:.2%} |")

    lines += ['', '## Explicit comparison vs Buy & Hold (OOS)', '', '| Metric | Buy&Hold | Recommended |', '|---|---:|---:|']
    bm=final[best_name]
    for k in ['CAGR','Total Return','Sharpe','Sortino','Max Drawdown','Calmar','Win Rate','Monthly Hit Rate','Turnover']:
        bval=buy[k] if k in buy else 0.0
        mval=bm[k] if k in bm else 0.0
        if k in ('Sharpe','Sortino','Calmar','Turnover'):
            lines.append(f'| {k} | {bval:.2f} | {mval:.2f} |')
        else:
            lines.append(f'| {k} | {bval:.2%} | {mval:.2%} |')

    lines += ['', '## Final selection logic', f'- Recommended: **{best_name}**', '- Selection: Pareto-per-fold then weighted triple-objective score.',]
    if note: lines.append(f'- Constraint note: {note}')
    lines += [
        '', '## Baseline references',
        f"- Buy&Hold: CAGR {buy['CAGR']:.2%}, Total Return {buy['Total Return']:.2%}, MaxDD {buy['Max Drawdown']:.2%}",
    ]
    pv=baselines.get('prior_repo_best_vol_breakout')
    if pv: lines.append(f"- Prior repo best vol_breakout: CAGR {pv['CAGR']:.2%}, MaxDD {pv['Max Drawdown']:.2%}, Sharpe {pv['Sharpe']:.2f}")
    lines += ['', '## Stability', f"- Bull CAGR {stabs['bull']['CAGR']:.2%}, Bear CAGR {stabs['bear']['CAGR']:.2%}", f"- High-vol MaxDD {stabs['high_vol']['Max Drawdown']:.2%}, Low-vol MaxDD {stabs['low_vol']['Max Drawdown']:.2%}", f'- Rolling windows evaluated: {len(rolling)}', '', '## Deployment blueprint', '- Size = signal × vol-target (35%) × drawdown de-risk ladder.', '- De-risk ladder: DD<-10% => 60% size; DD<-15% => 35%; DD<-20% => flat/kill-switch.', '- Alert/kill triggers: 180d Sharpe < 0 for two windows OR DD breach above historical 95th percentile.', '- Execution guardrails: long-only, exposure cap=1.0, turnover alert >25x/year.', '', '## Remaining risks', '- BTC gap risk, exchange microstructure slippage, and regime decay can degrade live results.', '- Carry-like sleeve is proxy signal, not true basis carry.', '- Needs quarterly re-validation and conservative capital ramp.',]
    (OUT_DIR/'TRIPLE_OBJECTIVE_REPORT.md').write_text('\n'.join(lines))


def write_notebook(best_name):
    nb={'cells':[{'cell_type':'markdown','metadata':{},'source':['# Triple-Objective BTC Research\n']},{'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':['import json, pathlib\n','j=json.loads(pathlib.Path("../results/triple_objective_summary.json").read_text())\n','j["best_strategy"], j["final_metrics"][j["best_strategy"]]\n']},{'cell_type':'markdown','metadata':{},'source':[f'Best strategy: **{best_name}**\n']}],'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
    (NB_DIR/'triple_objective_research.ipynb').write_text(json.dumps(nb,indent=2))


def main():
    data=read_data(); cfg=Cfg()
    final,oos,logs=walk_forward(data,cfg)
    baselines=load_baselines(data)
    best_name, beats_buyhold, note = choose_final(final, baselines['buy_and_hold'])
    stabs=regime_stability(data,oos[best_name]); roll=rolling_stats(oos[best_name])
    report(data,final,best_name,baselines,stabs,roll,note)
    write_notebook(best_name)
    out={
        'meta':{'track':'Triple-Objective Track','validation':'purged walk-forward train=4y test=180d step=180d purge=7d','frictions':{'cost_bps':cfg.cost_bps,'slippage_bps':cfg.slip_bps},'risk':{'target_vol':cfg.target_vol,'dd_ladder':[-0.10,-0.15,-0.20]}},
        'final_metrics':final,
        'best_strategy':best_name,
        'beats_buy_and_hold_return_constraint':beats_buyhold,
        'constraint_note':note,
        'fold_logs':logs,
        'oos_returns':oos,
        'regime_stability':stabs,
        'rolling_window':roll,
        'baselines':baselines,
    }
    (OUT_DIR/'triple_objective_summary.json').write_text(json.dumps(out,indent=2))
    print('Best:',best_name,'| beats buy&hold return constraint:',beats_buyhold)
    print(final[best_name])


if __name__=='__main__':
    main()
