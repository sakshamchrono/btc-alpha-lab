#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, statistics as stats
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / 'data' / 'btc_usd_daily_stooq.csv'
OUT_DIR = ROOT / 'results' / 'fib-pivot-halving-track'
NB_DIR = ROOT / 'notebooks'
OUT_DIR.mkdir(parents=True, exist_ok=True)
NB_DIR.mkdir(parents=True, exist_ok=True)


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
        out.append(close[i] / close[i - 1] - 1.0 if close[i - 1] else 0.0)
    return out


def ema(x, n):
    out = [x[0]]
    a = 2.0 / (n + 1)
    for i in range(1, len(x)):
        out.append(a * x[i] + (1 - a) * out[-1])
    return out


def rolling_std(x, n):
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        out[i] = stats.pstdev(w) if len(w) > 1 else 0.0
    return out


def rolling_max(x, n):
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        out[i] = max(x[i - n + 1:i + 1])
    return out


def rolling_min(x, n):
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        out[i] = min(x[i - n + 1:i + 1])
    return out


def rsi(close, p=14):
    out = [None] * len(close)
    g, l = [0.0] * len(close), [0.0] * len(close)
    for i in range(1, len(close)):
        d = close[i] - close[i - 1]
        g[i], l[i] = max(0.0, d), max(0.0, -d)
    ag = al = 0.0
    for i in range(1, len(close)):
        if i <= p:
            ag += g[i]
            al += l[i]
            if i == p:
                ag /= p
                al /= p
        else:
            ag = (ag * (p - 1) + g[i]) / p
            al = (al * (p - 1) + l[i]) / p
        if i >= p:
            out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    return out


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def shift(x, k=1):
    return ([0.0] * k + x[:-k]) if k > 0 else x[:]


def perf_stats(rets, ppy=365):
    if not rets:
        return {'Total Return': 0, 'CAGR': 0, 'Sharpe': 0, 'Sortino': 0, 'Max Drawdown': 0, 'Calmar': 0, 'Win Rate': 0, 'Monthly Hit Rate': 0, 'Ann.Vol': 0}
    eq, curve = 1.0, []
    for r in rets:
        eq *= 1 + r
        curve.append(eq)
    years = len(rets) / ppy
    cagr = eq ** (1 / years) - 1 if years > 0 and eq > 0 else 0
    vol = stats.pstdev(rets) if len(rets) > 1 else 0
    sharpe = (stats.mean(rets) / vol) * math.sqrt(ppy) if vol > 1e-12 else 0
    d = [min(0.0, r) for r in rets]
    dvol = stats.pstdev(d) if len(d) > 1 else 0
    sortino = (stats.mean(rets) / dvol) * math.sqrt(ppy) if dvol > 1e-12 else 0
    peak, mdd = -1e18, 0.0
    for e in curve:
        peak = max(peak, e)
        mdd = min(mdd, e / peak - 1)
    calmar = cagr / abs(mdd) if mdd < 0 else 0
    win = sum(1 for r in rets if r > 0) / len(rets)
    monthly, cur = [], 1.0
    for i, r in enumerate(rets, 1):
        cur *= 1 + r
        if i % 30 == 0:
            monthly.append(cur - 1)
            cur = 1.0
    mhr = sum(1 for x in monthly if x > 0) / len(monthly) if monthly else 0
    return {'Total Return': eq - 1, 'CAGR': cagr, 'Sharpe': sharpe, 'Sortino': sortino, 'Max Drawdown': mdd, 'Calmar': calmar, 'Win Rate': win, 'Monthly Hit Rate': mhr, 'Ann.Vol': vol * math.sqrt(ppy)}


def apply_costs(raw_rets, pos, cost_bps, slip_bps):
    fee = (cost_bps + slip_bps) / 10000.0
    prev, out, turn = 0.0, [], 0.0
    for r, p in zip(raw_rets, pos):
        t = abs(p - prev)
        turn += t
        out.append(r - t * fee)
        prev = p
    ann_turn = turn / max(1, len(pos)) * 365.0
    return out, ann_turn


def sigmoid(z):
    if z >= 0:
        ez = math.exp(-z)
        return 1 / (1 + ez)
    ez = math.exp(z)
    return ez / (1 + ez)


def standardize_fit(X):
    mu, sd = [], []
    for j in range(len(X[0])):
        col = [r[j] for r in X]
        m = stats.mean(col)
        s = stats.pstdev(col)
        mu.append(m)
        sd.append(s if s > 1e-12 else 1.0)
    return mu, sd


def standardize_apply(X, mu, sd):
    return [[(r[j] - mu[j]) / sd[j] for j in range(len(r))] for r in X]


def train_logistic(X, y, l2=1.0, lr=0.05, epochs=160):
    n, m = len(X), len(X[0])
    w = [0.0] * m
    for _ in range(epochs):
        g = [0.0] * m
        for xi, yi in zip(X, y):
            p = sigmoid(sum(a * b for a, b in zip(w, xi)))
            d = p - yi
            for j in range(m):
                g[j] += d * xi[j]
        for j in range(m):
            reg = l2 * w[j] if j < m - 1 else 0.0
            w[j] -= lr * ((g[j] / n) + reg / n)
    return w


def predict_logistic(X, w):
    return [sigmoid(sum(a * b for a, b in zip(w, x))) for x in X]


def risk_sized(raw_sig, rets, target_vol=0.35):
    pos, eq, peak = [], 1.0, 1.0
    for t, s in enumerate(raw_sig):
        vol = stats.pstdev(rets[max(0, t - 20):t + 1]) * math.sqrt(365) if t > 5 else 0.0
        vscale = clip(target_vol / vol, 0.0, 1.0) if vol > 1e-8 else 0.0
        dd = eq / peak - 1.0
        dscale = 1.0 if dd >= -0.10 else 0.6 if dd >= -0.15 else 0.35 if dd >= -0.20 else 0.0
        p = clip(s, 0.0, 1.0) * vscale * dscale
        pos.append(p)
        if t > 0:
            eq *= 1 + p * rets[t]
            peak = max(peak, eq)
    sh = shift(pos, 1)
    return [p * r for p, r in zip(sh, rets)], sh


def precompute(data):
    close = [x['close'] for x in data]
    high = [x['high'] for x in data]
    low = [x['low'] for x in data]
    ret = returns(close)
    return {
        'close': close,
        'high': high,
        'low': low,
        'ret': ret,
        'ema50': ema(close, 50),
        'ema200': ema(close, 200),
        'rv20': rolling_std(ret, 20),
        'rsi14': rsi(close, 14),
        'swing_h_90': rolling_max(high, 90),
        'swing_l_90': rolling_min(low, 90),
    }


def fib_features(i, ind):
    c = ind['close'][i]
    h = ind['swing_h_90'][i - 1] if i > 0 else None
    l = ind['swing_l_90'][i - 1] if i > 0 else None
    if h is None or l is None:
        return [0.0] * 8
    rng = max(1e-9, h - l)
    npx = (c - l) / rng
    lv = [0.236, 0.382, 0.5, 0.618, 0.786]
    d = [npx - x for x in lv]
    nearest = min(abs(x) for x in d)
    ext_127 = (c - (h + 0.272 * rng)) / rng
    ext_161 = (c - (h + 0.618 * rng)) / rng
    return [npx - 0.5, d[0], d[3], nearest, 1.0 if npx > 0.618 else 0.0, 1.0 if npx < 0.382 else 0.0, ext_127, ext_161]


def _prev_week_ohlc(data):
    wk = []
    cur_key = None
    o = h = l = c = None
    for row in data:
        y, w, _ = row['date'].isocalendar()
        key = (y, w)
        if cur_key is None:
            cur_key = key
            o = h = l = c = row['open']
            h = row['high']
            l = row['low']
            c = row['close']
        elif key == cur_key:
            h = max(h, row['high'])
            l = min(l, row['low'])
            c = row['close']
        else:
            wk.append((cur_key, (o, h, l, c)))
            cur_key = key
            o = row['open']
            h = row['high']
            l = row['low']
            c = row['close']
    if cur_key is not None:
        wk.append((cur_key, (o, h, l, c)))

    week_map = {}
    prev = None
    for key, ohlc in wk:
        week_map[key] = prev
        prev = ohlc
    return week_map


def pivot_levels(h, l, c):
    pp = (h + l + c) / 3.0
    r1 = 2 * pp - l
    s1 = 2 * pp - h
    r2 = pp + (h - l)
    s2 = pp - (h - l)
    return pp, r1, s1, r2, s2


def pivot_features(i, data, week_prev):
    if i == 0:
        return [0.0] * 12
    c = data[i]['close']

    pd = data[i - 1]
    dpp, dr1, ds1, dr2, ds2 = pivot_levels(pd['high'], pd['low'], pd['close'])
    drng = max(1e-9, pd['high'] - pd['low'])

    key = data[i]['date'].isocalendar()[:2]
    pw = week_prev.get(key)
    if pw is None:
        wpp = wr1 = ws1 = wr2 = ws2 = c
        wrng = max(1e-9, c * 0.01)
    else:
        wpp, wr1, ws1, wr2, ws2 = pivot_levels(pw[1], pw[2], pw[3])
        wrng = max(1e-9, pw[1] - pw[2])

    return [
        (c - dpp) / drng, (c - dr1) / drng, (c - ds1) / drng, (c - dr2) / drng, (c - ds2) / drng,
        1.0 if c > dpp else 0.0,
        (c - wpp) / wrng, (c - wr1) / wrng, (c - ws1) / wrng, (c - wr2) / wrng, (c - ws2) / wrng,
        1.0 if c > wpp else 0.0,
    ]


def halving_features(d: date):
    halvings = [date(2012, 11, 28), date(2016, 7, 9), date(2020, 5, 11), date(2024, 4, 20), date(2028, 4, 20)]
    prev_h = halvings[0]
    next_h = halvings[-1]
    for h in halvings:
        if h <= d:
            prev_h = h
        if h > d:
            next_h = h
            break
    days_since = (d - prev_h).days
    days_to = (next_h - d).days if next_h > d else 0
    cycle = clip(days_since / 1460.0, 0.0, 1.5)
    is_post_1y = 1.0 if 0 <= days_since <= 365 else 0.0
    is_mid = 1.0 if 365 < days_since <= 900 else 0.0
    is_late = 1.0 if 900 < days_since <= 1460 else 0.0
    near_halving = 1.0 if days_to <= 120 else 0.0
    sin_c = math.sin(2.0 * math.pi * clip(days_since / 1460.0, 0, 1))
    cos_c = math.cos(2.0 * math.pi * clip(days_since / 1460.0, 0, 1))
    return [cycle, days_to / 1460.0, is_post_1y, is_mid, is_late, near_halving, sin_c, cos_c]


def base_features(i, ind):
    c = ind['close']
    rv = (ind['rv20'][i] or 0.0) * math.sqrt(365)
    return [
        c[i] / c[i - 5] - 1.0,
        c[i] / c[i - 20] - 1.0,
        c[i] / c[i - 60] - 1.0,
        c[i] / ind['ema50'][i] - 1.0,
        c[i] / ind['ema200'][i] - 1.0,
        rv,
        (ind['rsi14'][i] or 50.0) / 100.0 - 0.5,
        sum(ind['ret'][i - k] for k in range(1, 8)),
    ]


def build_dataset(data, include_fib=False, include_pivot=False, include_halving=False):
    ind = precompute(data)
    week_prev = _prev_week_ohlc(data)
    X, y, idx = [], [], []
    start = 220
    for i in range(start, len(data) - 1):
        feat = base_features(i, ind)
        if include_fib:
            feat.extend(fib_features(i, ind))
        if include_pivot:
            feat.extend(pivot_features(i, data, week_prev))
        if include_halving:
            feat.extend(halving_features(data[i]['date']))
        feat.append(1.0)
        X.append(feat)
        y.append(1 if ind['ret'][i + 1] > 0 else 0)
        idx.append(i)
    return X, y, idx, ind['ret']


@dataclass
class Cfg:
    train: int = 365 * 4
    test: int = 180
    step: int = 180
    purge: int = 7
    cost_bps: float = 4.0
    slip_bps: float = 2.0
    target_vol: float = 0.35
    l2: float = 1.2
    entry: float = 0.525


def run_variant(name, flags, data, cfg):
    X, y, idx_map, all_rets = build_dataset(data, **flags)
    idx_to_pos = {idx: i for i, idx in enumerate(idx_map)}

    oos_rets = []
    fold_logs = []
    turns = []
    oos_market = []

    i = 0
    while True:
        ts = i
        te = ts + cfg.train
        qs = te + cfg.purge
        qe = qs + cfg.test
        if qe >= len(data):
            break

        tr_end_idx = te - 1
        q_start_idx = qs
        q_end_idx = qe - 1

        if tr_end_idx not in idx_to_pos or q_start_idx not in idx_to_pos or q_end_idx not in idx_to_pos:
            i += cfg.step
            continue

        tr0 = idx_to_pos[max(220, ts)]
        tr1 = idx_to_pos[tr_end_idx]
        te0 = idx_to_pos[q_start_idx]
        te1 = idx_to_pos[q_end_idx] + 1

        Xtr, ytr = X[tr0:tr1], y[tr0:tr1]
        Xte = X[te0:te1]

        if len(Xtr) < 250 or len(Xte) < 30:
            i += cfg.step
            continue

        mu, sd = standardize_fit(Xtr)
        Xtrs = standardize_apply(Xtr, mu, sd)
        Xtes = standardize_apply(Xte, mu, sd)
        w = train_logistic(Xtrs, ytr, l2=cfg.l2, lr=0.05, epochs=170)
        p = predict_logistic(Xtes, w)

        sig = [clip((x - cfg.entry) * 2.4, 0.0, 1.0) for x in p]
        rr = all_rets[qs:qe]
        raw, pos = risk_sized(sig, rr, target_vol=cfg.target_vol)
        net, turn = apply_costs(raw, pos, cfg.cost_bps, cfg.slip_bps)

        oos_rets.extend(net)
        oos_market.extend(rr)
        turns.append(turn)
        fold_logs.append({
            'train_start': data[ts]['date'].isoformat(),
            'train_end': data[te - 1]['date'].isoformat(),
            'test_start': data[qs]['date'].isoformat(),
            'test_end': data[qe - 1]['date'].isoformat(),
            'n_train': len(Xtr),
            'n_test': len(Xte),
            'turnover': turn,
        })
        i += cfg.step

    m = perf_stats(oos_rets)
    m['Turnover'] = stats.mean(turns) if turns else 0.0
    return {
        'name': name,
        'flags': flags,
        'metrics': m,
        'oos_returns': oos_rets,
        'oos_market_returns': oos_market,
        'fold_logs': fold_logs,
    }


def fmt_pct(x):
    return f'{x:.2%}'


def fmt_num(x):
    return f'{x:.2f}'


def load_latest_recommended():
    p = ROOT / 'results' / 'lowdd_summary.json'
    if not p.exists():
        return None
    j = json.loads(p.read_text())
    ranked = j.get('ranked', [])
    if not ranked:
        return None
    best = ranked[0]['strategy']
    m = j.get('metrics_oos', {}).get(best)
    if not m:
        return None
    return {'track': 'lowdd', 'strategy': best, 'metrics': m}


def make_report(data, results, buyhold, latest):
    ordered = ['baseline', 'plus_fib', 'plus_pivots', 'plus_halving', 'combined']
    names = {
        'baseline': 'Baseline',
        'plus_fib': 'Baseline + Fibonacci',
        'plus_pivots': 'Baseline + Pivots',
        'plus_halving': 'Baseline + Halving',
        'combined': 'Combined (Fib+Pivots+Halving)',
    }
    lines = [
        '# Fib-Pivot-Halving Track',
        '',
        f"Data: {data[0]['date']} to {data[-1]['date']} ({len(data)} rows)",
        'Validation: purged walk-forward (train=4y, test=180d, step=180d, purge=7d)',
        'Frictions: 4 bps costs + 2 bps slippage',
        '',
        '## Ablation (OOS)',
        '',
        '| Variant | CAGR | Total Return | Sharpe | Sortino | MaxDD | Calmar | Win Rate | Monthly Hit | Turnover |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for k in ordered:
        m = results[k]['metrics']
        lines.append(
            f"| {names[k]} | {m['CAGR']:.2%} | {m['Total Return']:.2%} | {m['Sharpe']:.2f} | {m['Sortino']:.2f} | {m['Max Drawdown']:.2%} | {m['Calmar']:.2f} | {m['Win Rate']:.2%} | {m['Monthly Hit Rate']:.2%} | {m['Turnover']:.2f}x |"
        )

    c = results['combined']['metrics']
    b = results['baseline']['metrics']
    lines += [
        '',
        '## Combined vs Baseline delta',
        f"- CAGR: {c['CAGR'] - b['CAGR']:+.2%}",
        f"- Win Rate: {c['Win Rate'] - b['Win Rate']:+.2%}",
        f"- Max Drawdown improvement (less negative is better): {abs(b['Max Drawdown']) - abs(c['Max Drawdown']):+.2%}",
        '',
        '## Benchmarks',
        '',
        '| Metric | Buy & Hold (same OOS windows) | Combined |',
        '|---|---:|---:|',
    ]
    for k in ['CAGR', 'Total Return', 'Sharpe', 'Sortino', 'Max Drawdown', 'Calmar', 'Win Rate', 'Monthly Hit Rate', 'Turnover']:
        bv = buyhold.get(k, 0.0)
        cv = c.get(k, 0.0)
        if k in ('Sharpe', 'Sortino', 'Calmar', 'Turnover'):
            lines.append(f'| {k} | {bv:.2f} | {cv:.2f} |')
        else:
            lines.append(f'| {k} | {bv:.2%} | {cv:.2%} |')

    if latest:
        lm = latest['metrics']
        lines += [
            '',
            f"## Latest recommended strategy reference ({latest['track']}::{latest['strategy']})",
            '',
            '| Metric | Latest Recommended | Combined |',
            '|---|---:|---:|',
        ]
        for k in ['CAGR', 'Total Return', 'Sharpe', 'Sortino', 'Max Drawdown', 'Calmar', 'Win Rate', 'Monthly Hit Rate', 'Turnover']:
            lv = lm.get(k, 0.0)
            cv = c.get(k, 0.0)
            if k in ('Sharpe', 'Sortino', 'Calmar', 'Turnover'):
                lines.append(f'| {k} | {lv:.2f} | {cv:.2f} |')
            else:
                lines.append(f'| {k} | {lv:.2%} | {cv:.2%} |')

    (OUT_DIR / 'REPORT.md').write_text('\n'.join(lines))


def write_notebook():
    nb = {
        'cells': [
            {'cell_type': 'markdown', 'metadata': {}, 'source': ['# Fib-Pivot-Halving Track\n', 'Ablation study over BTC daily OOS walk-forward.\n']},
            {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': [
                'import json, pathlib\n',
                'j=json.loads(pathlib.Path("../results/fib-pivot-halving-track/summary.json").read_text())\n',
                'j["ablation_table"]\n'
            ]},
        ],
        'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}},
        'nbformat': 4,
        'nbformat_minor': 5
    }
    (NB_DIR / 'fib_pivot_halving_track.ipynb').write_text(json.dumps(nb, indent=2))


def main():
    data = read_data()
    cfg = Cfg()

    variants = {
        'baseline': {'include_fib': False, 'include_pivot': False, 'include_halving': False},
        'plus_fib': {'include_fib': True, 'include_pivot': False, 'include_halving': False},
        'plus_pivots': {'include_fib': False, 'include_pivot': True, 'include_halving': False},
        'plus_halving': {'include_fib': False, 'include_pivot': False, 'include_halving': True},
        'combined': {'include_fib': True, 'include_pivot': True, 'include_halving': True},
    }

    results = {k: run_variant(k, v, data, cfg) for k, v in variants.items()}

    buyhold = perf_stats(results['combined']['oos_market_returns'])
    buyhold['Turnover'] = 1.0

    latest = load_latest_recommended()
    make_report(data, results, buyhold, latest)
    write_notebook()

    ablation = {k: results[k]['metrics'] for k in variants}

    out = {
        'meta': {
            'track': 'fib-pivot-halving-track',
            'validation': 'purged walk-forward train=4y test=180d step=180d purge=7d',
            'frictions': {'cost_bps': cfg.cost_bps, 'slippage_bps': cfg.slip_bps},
            'risk': {'target_vol': cfg.target_vol, 'dd_ladder': [-0.10, -0.15, -0.20]},
        },
        'ablation_table': ablation,
        'variants': results,
        'benchmarks': {
            'buy_and_hold_same_oos_windows': buyhold,
            'latest_recommended_strategy': latest,
        },
        'material_help_test': {
            'combined_vs_baseline': {
                'cagr_delta': results['combined']['metrics']['CAGR'] - results['baseline']['metrics']['CAGR'],
                'win_rate_delta': results['combined']['metrics']['Win Rate'] - results['baseline']['metrics']['Win Rate'],
                'maxdd_improvement': abs(results['baseline']['metrics']['Max Drawdown']) - abs(results['combined']['metrics']['Max Drawdown']),
            }
        }
    }

    (OUT_DIR / 'summary.json').write_text(json.dumps(out, indent=2))

    print('Ablation complete.')
    for k in ['baseline', 'plus_fib', 'plus_pivots', 'plus_halving', 'combined']:
        m = results[k]['metrics']
        print(k, 'CAGR', f"{m['CAGR']:.2%}", 'Win', f"{m['Win Rate']:.2%}", 'MaxDD', f"{m['Max Drawdown']:.2%}")


if __name__ == '__main__':
    main()
