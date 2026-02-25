#!/usr/bin/env python3
"""BTC alpha lab using only Python stdlib.

Implements walk-forward backtests for 3 strategy families:
- Trend following (MA crossover)
- Mean reversion (RSI)
- Volatility breakout regime (Donchian + long EMA filter)

Data source: Stooq daily BTCUSD CSV.
"""

from __future__ import annotations
import csv
import json
import math
import statistics as stats
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "results"
DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)


def fetch_btc_daily() -> list[dict]:
    url = "https://stooq.com/q/d/l/?s=btcusd&i=d"
    raw = urllib.request.urlopen(url, timeout=30).read().decode("utf-8").strip().splitlines()
    rows = list(csv.DictReader(raw))
    out = []
    for r in rows:
        try:
            out.append(
                {
                    "date": datetime.strptime(r["Date"], "%Y-%m-%d").date(),
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                }
            )
        except Exception:
            continue
    out.sort(key=lambda x: x["date"])
    return out


def returns(close: list[float]) -> list[float]:
    out = [0.0]
    for i in range(1, len(close)):
        prev = close[i - 1]
        out.append((close[i] / prev) - 1.0 if prev else 0.0)
    return out


def sma(arr: list[float], n: int) -> list[float | None]:
    out = [None] * len(arr)
    if n <= 0:
        return out
    s = 0.0
    for i, v in enumerate(arr):
        s += v
        if i >= n:
            s -= arr[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(arr: list[float], n: int) -> list[float]:
    out = [arr[0]]
    a = 2.0 / (n + 1)
    for i in range(1, len(arr)):
        out.append(a * arr[i] + (1 - a) * out[-1])
    return out


def rsi(arr: list[float], period: int = 14) -> list[float | None]:
    out = [None] * len(arr)
    gains = [0.0] * len(arr)
    losses = [0.0] * len(arr)
    for i in range(1, len(arr)):
        d = arr[i] - arr[i - 1]
        gains[i] = max(d, 0.0)
        losses[i] = max(-d, 0.0)
    avg_gain = 0.0
    avg_loss = 0.0
    for i in range(1, len(arr)):
        if i <= period:
            avg_gain += gains[i]
            avg_loss += losses[i]
            if i == period:
                avg_gain /= period
                avg_loss /= period
        else:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if i >= period:
            if avg_loss == 0:
                out[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def perf_stats(rets: list[float], periods_per_year: int = 365) -> dict:
    if not rets:
        return {"Total Return": 0, "CAGR": 0, "Sharpe": 0, "Ann.Vol": 0, "Max Drawdown": 0, "Win Rate": 0}
    equity = []
    eq = 1.0
    for r in rets:
        eq *= 1 + r
        equity.append(eq)
    total_ret = equity[-1] - 1.0
    years = len(rets) / periods_per_year if periods_per_year else 0
    cagr = equity[-1] ** (1 / years) - 1 if years > 0 and equity[-1] > 0 else 0.0
    vol = stats.pstdev(rets) * math.sqrt(periods_per_year) if len(rets) > 1 else 0.0
    sharpe = (stats.mean(rets) / stats.pstdev(rets)) * math.sqrt(periods_per_year) if len(rets) > 1 and stats.pstdev(rets) > 0 else 0.0
    peak = -1e18
    max_dd = 0.0
    for x in equity:
        peak = max(peak, x)
        dd = x / peak - 1.0
        if dd < max_dd:
            max_dd = dd
    win_rate = sum(1 for r in rets if r > 0) / len(rets)
    return {
        "Total Return": total_ret,
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Ann.Vol": vol,
        "Max Drawdown": max_dd,
        "Win Rate": win_rate,
    }


def apply_costs(raw_rets: list[float], pos: list[float], cost_bps: float) -> list[float]:
    out = []
    prev = 0.0
    c = cost_bps / 10000.0
    for r, p in zip(raw_rets, pos):
        turnover = abs(p - prev)
        out.append(r - turnover * c)
        prev = p
    return out


def trend_signal(close: list[float], fast: int, slow: int) -> list[float]:
    f = sma(close, fast)
    s = sma(close, slow)
    sig = []
    for i in range(len(close)):
        if f[i] is None or s[i] is None:
            sig.append(0.0)
        else:
            sig.append(1.0 if f[i] > s[i] else 0.0)
    return sig


def meanrev_signal(close: list[float], rsi_period: int, low: float, high: float) -> list[float]:
    rv = rsi(close, rsi_period)
    sig = []
    state = 0.0
    for x in rv:
        if x is not None and x < low:
            state = 1.0
        elif x is not None and x > high:
            state = 0.0
        sig.append(state)
    return sig


def rolling_max(arr: list[float], n: int) -> list[float | None]:
    out = [None] * len(arr)
    for i in range(n - 1, len(arr)):
        out[i] = max(arr[i - n + 1 : i + 1])
    return out


def rolling_min(arr: list[float], n: int) -> list[float | None]:
    out = [None] * len(arr)
    for i in range(n - 1, len(arr)):
        out[i] = min(arr[i - n + 1 : i + 1])
    return out


def breakout_signal(high: list[float], low: list[float], close: list[float], lookback: int, ema_regime: int) -> list[float]:
    h = rolling_max(high, lookback)
    l = rolling_min(low, lookback)
    e = ema(close, ema_regime)
    sig = []
    state = 0.0
    for i in range(len(close)):
        h_prev = h[i - 1] if i > 0 else None
        l_prev = l[i - 1] if i > 0 else None
        if h_prev is not None and close[i] > h_prev and close[i] > e[i]:
            state = 1.0
        elif l_prev is not None and close[i] < l_prev:
            state = 0.0
        sig.append(state)
    return sig


def shift(sig: list[float], k: int = 1) -> list[float]:
    if k <= 0:
        return sig[:]
    return [0.0] * k + sig[:-k]


def strat_returns(sig: list[float], rets: list[float], cost_bps: float) -> list[float]:
    pos = shift(sig, 1)
    raw = [p * r for p, r in zip(pos, rets)]
    return apply_costs(raw, pos, cost_bps)


@dataclass
class WF:
    train: int = 365 * 3
    test: int = 365
    step: int = 365
    cost_bps: float = 5.0


def walk_forward(data: list[dict], strategy_name: str, param_grid: list[dict], signal_fn, cfg: WF) -> tuple[list[dict], list[float]]:
    close = [r["close"] for r in data]
    high = [r["high"] for r in data]
    low = [r["low"] for r in data]
    rets = returns(close)

    logs = []
    oos_rets = []
    oos_dates = []

    i = 0
    while True:
        train_end = i + cfg.train
        test_end = train_end + cfg.test
        if test_end >= len(data):
            break

        best = None
        best_sharpe = -1e18
        train_slice = slice(i, train_end)
        test_slice = slice(train_end, test_end)

        for p in param_grid:
            if strategy_name == "vol_breakout":
                sig = signal_fn(high[train_slice], low[train_slice], close[train_slice], **p)
            else:
                sig = signal_fn(close[train_slice], **p)
            sret = strat_returns(sig, rets[train_slice], cfg.cost_bps)
            sh = perf_stats(sret)["Sharpe"]
            if sh > best_sharpe:
                best_sharpe = sh
                best = p

        if strategy_name == "vol_breakout":
            sig_test = signal_fn(high[test_slice], low[test_slice], close[test_slice], **best)
        else:
            sig_test = signal_fn(close[test_slice], **best)
        r_test = strat_returns(sig_test, rets[test_slice], cfg.cost_bps)

        oos_rets.extend(r_test)
        oos_dates.extend([d["date"].isoformat() for d in data[test_slice]])
        logs.append(
            {
                "strategy": strategy_name,
                "train_start": data[i]["date"].isoformat(),
                "train_end": data[train_end - 1]["date"].isoformat(),
                "test_start": data[train_end]["date"].isoformat(),
                "test_end": data[test_end - 1]["date"].isoformat(),
                "best_param": best,
                "train_sharpe": best_sharpe,
            }
        )
        i += cfg.step

    return logs, [{"date": d, "ret": r} for d, r in zip(oos_dates, oos_rets)]


def summarize_cost_sensitivity(data, selections, strategy_name, signal_fn, levels=(2, 5, 10, 20)):
    close = [r["close"] for r in data]
    high = [r["high"] for r in data]
    low = [r["low"] for r in data]
    rets = returns(close)
    out = []
    for c in levels:
        all_rets = []
        for w in selections:
            s = next(i for i, r in enumerate(data) if r["date"].isoformat() == w["test_start"])
            e = next(i for i, r in enumerate(data) if r["date"].isoformat() == w["test_end"])
            sl = slice(s, e + 1)
            p = w["best_param"]
            if strategy_name == "vol_breakout":
                sig = signal_fn(high[sl], low[sl], close[sl], **p)
            else:
                sig = signal_fn(close[sl], **p)
            all_rets.extend(strat_returns(sig, rets[sl], c))
        m = perf_stats(all_rets)
        out.append({"cost_bps": c, "Sharpe": m["Sharpe"], "CAGR": m["CAGR"], "MaxDD": m["Max Drawdown"]})
    return out


def main():
    data = fetch_btc_daily()
    with open(DATA_DIR / "btc_usd_daily_stooq.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close"])
        for r in data:
            w.writerow([r["date"].isoformat(), r["open"], r["high"], r["low"], r["close"]])

    cfg = WF()

    trend_grid = [{"fast": f, "slow": s} for f, s in product([10, 20, 30, 50], [80, 100, 150, 200]) if f < s]
    mr_grid = [
        {"rsi_period": p, "low": l, "high": h}
        for p, l, h in product([7, 14, 21], [20, 25, 30, 35], [50, 55, 60])
        if l < h
    ]
    br_grid = [{"lookback": lb, "ema_regime": em} for lb, em in product([10, 20, 40, 60], [100, 150, 200, 250])]

    t_sel, t_oos = walk_forward(data, "trend_following", trend_grid, trend_signal, cfg)
    m_sel, m_oos = walk_forward(data, "mean_reversion", mr_grid, meanrev_signal, cfg)
    b_sel, b_oos = walk_forward(data, "vol_breakout", br_grid, breakout_signal, cfg)

    metrics = {
        "trend_following": perf_stats([x["ret"] for x in t_oos]),
        "mean_reversion": perf_stats([x["ret"] for x in m_oos]),
        "vol_breakout": perf_stats([x["ret"] for x in b_oos]),
    }

    sensitivity = {
        "trend_following": summarize_cost_sensitivity(data, t_sel, "trend_following", trend_signal),
        "mean_reversion": summarize_cost_sensitivity(data, m_sel, "mean_reversion", meanrev_signal),
        "vol_breakout": summarize_cost_sensitivity(data, b_sel, "vol_breakout", breakout_signal),
    }

    out = {
        "meta": {
            "data_rows": len(data),
            "date_start": data[0]["date"].isoformat(),
            "date_end": data[-1]["date"].isoformat(),
            "assumptions": {
                "signal_lag_days": 1,
                "transaction_cost_bps": cfg.cost_bps,
                "validation": "walk-forward train=3y test=1y step=1y",
                "positioning": "long/flat",
            },
        },
        "metrics_oos": metrics,
        "selection_logs": {
            "trend_following": t_sel,
            "mean_reversion": m_sel,
            "vol_breakout": b_sel,
        },
        "oos_returns": {
            "trend_following": t_oos,
            "mean_reversion": m_oos,
            "vol_breakout": b_oos,
        },
        "cost_sensitivity": sensitivity,
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(out, indent=2))

    # quick markdown report
    def fmt(m):
        return f"CAGR={m['CAGR']:.2%}, Sharpe={m['Sharpe']:.2f}, MaxDD={m['Max Drawdown']:.2%}, WinRate={m['Win Rate']:.2%}"

    ranked = sorted(metrics.items(), key=lambda kv: kv[1]["Sharpe"], reverse=True)
    best_name, best_m = ranked[0]
    lines = [
        "# BTC Alpha Lab Results",
        "",
        f"Data: {out['meta']['date_start']} to {out['meta']['date_end']} ({out['meta']['data_rows']} daily rows)",
        "",
        "## OOS Metrics (walk-forward)",
    ]
    for k, v in ranked:
        lines.append(f"- **{k}**: {fmt(v)}")
    lines += [
        "",
        f"## Best strategy: {best_name}",
        f"- {fmt(best_m)}",
        "",
        "## Caveats",
        "- Regime shifts can invalidate historical edges.",
        "- Daily bars miss intraday slippage/liquidity shocks.",
        "- Live execution frictions may reduce realized Sharpe.",
        "- No guaranteed profits.",
    ]
    (OUT_DIR / "REPORT.md").write_text("\n".join(lines))

    print("Done. Best strategy:", best_name)
    print(fmt(best_m))


if __name__ == "__main__":
    main()
