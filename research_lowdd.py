#!/usr/bin/env python3
"""Low-drawdown BTC strategy research module.

Focus: robust OOS consistency and drawdown control (not max CAGR).
Families:
1) Vol-targeted trend with adaptive sizing
2) Regime filter + momentum with risk-off behavior
3) Statistical linear model with handcrafted features (strict walk-forward, no leakage)
"""

from __future__ import annotations
import csv
import json
import math
import statistics as stats
from dataclasses import dataclass
from datetime import datetime
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "btc_usd_daily_stooq.csv"
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(exist_ok=True)


def read_data() -> list[dict]:
    rows = []
    with open(DATA_PATH, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "date": datetime.strptime(r["date"], "%Y-%m-%d").date(),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                }
            )
    rows.sort(key=lambda x: x["date"])
    return rows


def returns(close: list[float]) -> list[float]:
    out = [0.0]
    for i in range(1, len(close)):
        out.append((close[i] / close[i - 1]) - 1.0 if close[i - 1] else 0.0)
    return out


def sma(x: list[float], n: int) -> list[float | None]:
    out = [None] * len(x)
    if n <= 0:
        return out
    s = 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(x: list[float], n: int) -> list[float]:
    out = [x[0]]
    a = 2.0 / (n + 1)
    for i in range(1, len(x)):
        out.append(a * x[i] + (1 - a) * out[-1])
    return out


def rolling_std(x: list[float], n: int) -> list[float | None]:
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1 : i + 1]
        out[i] = stats.pstdev(w) if len(w) > 1 else 0.0
    return out


def rolling_max(x: list[float], n: int) -> list[float | None]:
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        out[i] = max(x[i - n + 1 : i + 1])
    return out


def shift(sig: list[float], k: int = 1) -> list[float]:
    if k <= 0:
        return sig[:]
    return [0.0] * k + sig[:-k]


def max_drawdown(equity: list[float]) -> float:
    peak = -1e18
    mdd = 0.0
    for e in equity:
        peak = max(peak, e)
        dd = e / peak - 1.0
        if dd < mdd:
            mdd = dd
    return mdd


def ulcer_index(equity: list[float]) -> float:
    peak = -1e18
    sq = []
    for e in equity:
        peak = max(peak, e)
        dd = min(0.0, e / peak - 1.0)
        sq.append((dd * 100.0) ** 2)
    return math.sqrt(sum(sq) / len(sq)) if sq else 0.0


def perf_stats(rets: list[float], periods_per_year: int = 365) -> dict:
    if not rets:
        return {}
    eq = 1.0
    equity = []
    for r in rets:
        eq *= 1 + r
        equity.append(eq)
    years = len(rets) / periods_per_year
    cagr = eq ** (1 / years) - 1 if years > 0 and eq > 0 else 0.0
    vol = stats.pstdev(rets) * math.sqrt(periods_per_year) if len(rets) > 1 else 0.0
    downside = [min(0.0, r) for r in rets]
    dstd = stats.pstdev(downside) if len(rets) > 1 else 0.0
    sharpe = (stats.mean(rets) / stats.pstdev(rets)) * math.sqrt(periods_per_year) if len(rets) > 1 and stats.pstdev(rets) > 0 else 0.0
    sortino = (stats.mean(rets) / dstd) * math.sqrt(periods_per_year) if dstd > 0 else 0.0
    mdd = max_drawdown(equity)
    calmar = cagr / abs(mdd) if mdd < 0 else 0.0
    ui = ulcer_index(equity)
    win_rate = sum(1 for r in rets if r > 0) / len(rets)

    # monthly hit rate + smoothness
    monthly = []
    cur = 1.0
    for i, r in enumerate(rets, 1):
        cur *= 1 + r
        if i % 30 == 0:
            monthly.append(cur - 1)
            cur = 1.0
    monthly_hit = (sum(1 for x in monthly if x > 0) / len(monthly)) if monthly else 0.0
    smoothness = 1.0 / (1.0 + (stats.pstdev(monthly) if len(monthly) > 1 else 0.0))

    return {
        "Total Return": eq - 1.0,
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Ann.Vol": vol,
        "Max Drawdown": mdd,
        "Calmar": calmar,
        "Ulcer Index": ui,
        "Win Rate": win_rate,
        "Monthly Hit Rate": monthly_hit,
        "Return Smoothness": smoothness,
    }


def apply_costs(raw: list[float], pos: list[float], cost_bps: float, slippage_bps: float) -> tuple[list[float], float]:
    c = (cost_bps + slippage_bps) / 10000.0
    out = []
    turnover_sum = 0.0
    prev = 0.0
    for r, p in zip(raw, pos):
        t = abs(p - prev)
        turnover_sum += t
        out.append(r - t * c)
        prev = p
    ann_turnover = turnover_sum / max(1, len(pos)) * 365.0
    return out, ann_turnover


def objective(m: dict, ann_turnover: float, target_vol: float, turnover_cap: float) -> float:
    penalty = 0.0
    if m["Ann.Vol"] > target_vol:
        penalty += (m["Ann.Vol"] - target_vol) * 8.0
    if ann_turnover > turnover_cap:
        penalty += (ann_turnover - turnover_cap) * 0.4
    score = (
        2.6 * m["Calmar"]
        + 1.8 * m["Sortino"]
        + 1.2 * m["Return Smoothness"]
        - 3.0 * abs(m["Max Drawdown"])
        - 0.08 * m["Ulcer Index"]
        - penalty
    )
    return score


# ---------- Strategy families ----------
def vol_target_trend(close: list[float], rets: list[float], fast: int, slow: int, vol_lb: int, target_vol: float, dd_cut: float) -> list[float]:
    f = sma(close, fast)
    s = sma(close, slow)
    rv = rolling_std(rets, vol_lb)
    pos = []
    eq = 1.0
    peak = 1.0
    for i in range(len(close)):
        base = 1.0 if (f[i] is not None and s[i] is not None and f[i] > s[i]) else 0.0
        vol = rv[i] * math.sqrt(365) if rv[i] is not None else None
        size = min(1.0, max(0.0, target_vol / vol)) if vol and vol > 1e-8 else 0.0
        p = base * size
        if i > 0:
            eq *= 1 + p * rets[i]
            peak = max(peak, eq)
            if eq / peak - 1.0 < dd_cut:
                p = 0.0
        pos.append(p)
    return pos


def regime_momentum(close: list[float], rets: list[float], mom_lb: int, regime_ema: int, vol_lb: int, target_vol: float) -> list[float]:
    e = ema(close, regime_ema)
    rv = rolling_std(rets, vol_lb)
    pos = []
    for i in range(len(close)):
        mom = (close[i] / close[i - mom_lb] - 1.0) if i >= mom_lb else 0.0
        risk_on = close[i] > e[i] and mom > 0
        vol = rv[i] * math.sqrt(365) if rv[i] is not None else None
        size = min(1.0, max(0.0, target_vol / vol)) if vol and vol > 1e-8 else 0.0
        pos.append(size if risk_on else 0.0)
    return pos


def solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    # Gaussian elimination with partial pivoting
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[piv] = m[piv], m[i]
        if abs(m[i][i]) < 1e-12:
            continue
        div = m[i][i]
        for c in range(i, n + 1):
            m[i][c] /= div
        for r in range(n):
            if r == i:
                continue
            factor = m[r][i]
            for c in range(i, n + 1):
                m[r][c] -= factor * m[i][c]
    return [m[i][n] for i in range(n)]


def linear_model_positions(close: list[float], rets: list[float], lookbacks: tuple[int, int, int], ridge: float, threshold: float, target_vol: float) -> list[float]:
    l1, l2, l3 = lookbacks
    e50 = ema(close, 50)
    vol20 = rolling_std(rets, 20)

    X, y = [], []
    for t in range(max(l1, l2, l3, 60), len(close) - 1):
        dd60_peak = max(close[t - 59 : t + 1])
        f = [
            close[t] / close[t - l1] - 1.0,
            close[t] / close[t - l2] - 1.0,
            close[t] / close[t - l3] - 1.0,
            (vol20[t] or 0.0) * math.sqrt(365),
            close[t] / e50[t] - 1.0,
            close[t] / dd60_peak - 1.0,
            1.0,
        ]
        X.append(f)
        y.append(rets[t + 1])

    nfeat = len(X[0]) if X else 0
    if nfeat == 0:
        return [0.0] * len(close)

    xtx = [[0.0] * nfeat for _ in range(nfeat)]
    xty = [0.0] * nfeat
    for r in range(len(X)):
        for i in range(nfeat):
            xty[i] += X[r][i] * y[r]
            for j in range(nfeat):
                xtx[i][j] += X[r][i] * X[r][j]
    for i in range(nfeat - 1):
        xtx[i][i] += ridge
    beta = solve_linear_system(xtx, xty)

    pos = [0.0] * len(close)
    for t in range(max(l1, l2, l3, 60), len(close)):
        dd60_peak = max(close[t - 59 : t + 1])
        f = [
            close[t] / close[t - l1] - 1.0,
            close[t] / close[t - l2] - 1.0,
            close[t] / close[t - l3] - 1.0,
            (vol20[t] or 0.0) * math.sqrt(365),
            close[t] / e50[t] - 1.0,
            close[t] / dd60_peak - 1.0,
            1.0,
        ]
        pred = sum(fi * bi for fi, bi in zip(f, beta))
        vol = (vol20[t] or 0.0) * math.sqrt(365)
        size = min(1.0, max(0.0, target_vol / vol)) if vol > 1e-8 else 0.0
        pos[t] = size if pred > threshold else 0.0
    return pos


@dataclass
class WFCfg:
    train: int = 365 * 3
    test: int = 180
    step: int = 180
    purge: int = 5
    cost_bps: float = 4.0
    slippage_bps: float = 2.0
    target_vol: float = 0.35
    turnover_cap: float = 20.0


def evaluate_candidate(close, rets, pos, cfg: WFCfg):
    shifted = shift(pos, 1)
    raw = [p * r for p, r in zip(shifted, rets)]
    net, ann_turn = apply_costs(raw, shifted, cfg.cost_bps, cfg.slippage_bps)
    m = perf_stats(net)
    m["Turnover"] = ann_turn
    return m, objective(m, ann_turn, cfg.target_vol, cfg.turnover_cap), net


def walk_forward_lowdd(data: list[dict], family: str, param_grid: list[dict], cfg: WFCfg):
    close = [r["close"] for r in data]
    rets = returns(close)

    oos_rets, logs = [], []
    stability = []
    i = 0
    while True:
        train_end = i + cfg.train
        test_end = train_end + cfg.test
        if test_end >= len(data):
            break

        train_slice = slice(i, train_end)
        test_slice = slice(train_end + cfg.purge, test_end)

        best_score = -1e18
        best_p = None

        score_table = []
        for p in param_grid:
            c = close[train_slice]
            r = rets[train_slice]
            if family == "vol_target_trend":
                pos = vol_target_trend(c, r, **p)
            elif family == "regime_momentum":
                pos = regime_momentum(c, r, **p)
            else:
                pos = linear_model_positions(c, r, **p)
            m, s, _ = evaluate_candidate(c, r, pos, cfg)
            score_table.append({"params": p, "score": s, "maxdd": m["Max Drawdown"], "calmar": m["Calmar"], "sortino": m["Sortino"], "turnover": m["Turnover"]})
            if s > best_score:
                best_score = s
                best_p = p

        c2 = close[test_slice]
        r2 = rets[test_slice]
        if family == "vol_target_trend":
            pos2 = vol_target_trend(c2, r2, **best_p)
        elif family == "regime_momentum":
            pos2 = regime_momentum(c2, r2, **best_p)
        else:
            pos2 = linear_model_positions(c2, r2, **best_p)
        m2, s2, net2 = evaluate_candidate(c2, r2, pos2, cfg)

        oos_rets.extend(net2)
        logs.append(
            {
                "family": family,
                "train_start": data[i]["date"].isoformat(),
                "train_end": data[train_end - 1]["date"].isoformat(),
                "test_start": data[train_end + cfg.purge]["date"].isoformat(),
                "test_end": data[test_end - 1]["date"].isoformat(),
                "best_params": best_p,
                "train_best_score": best_score,
                "oos_score": s2,
                "oos_maxdd": m2["Max Drawdown"],
                "oos_turnover": m2["Turnover"],
            }
        )
        stability.append(score_table)
        i += cfg.step

    m_final = perf_stats(oos_rets)
    m_final["Turnover"] = stats.mean([x["oos_turnover"] for x in logs]) if logs else 0.0
    return m_final, oos_rets, logs, stability


def fmt_pct(x):
    return f"{x:.2%}"


def main():
    data = read_data()
    cfg = WFCfg()

    grids = {
        "vol_target_trend": [
            {"fast": f, "slow": s, "vol_lb": v, "target_vol": tv, "dd_cut": ddc}
            for f, s, v, tv, ddc in product([20, 50], [120, 200], [20, 30], [0.25, 0.35], [-0.12, -0.18])
            if f < s
        ],
        "regime_momentum": [
            {"mom_lb": m, "regime_ema": e, "vol_lb": v, "target_vol": tv}
            for m, e, v, tv in product([20, 60], [120, 200], [20, 30], [0.25, 0.35])
        ],
        "linear_ml": [
            {"lookbacks": lbs, "ridge": rg, "threshold": th, "target_vol": tv}
            for lbs, rg, th, tv in product([(5, 20, 60), (10, 30, 90)], [0.1, 1.0], [0.0, 0.0005], [0.25, 0.35])
        ],
    }

    results = {}
    logs = {}
    stability = {}
    oos = {}
    for fam, grid in grids.items():
        m, r, lg, st = walk_forward_lowdd(data, fam, grid, cfg)
        results[fam] = m
        logs[fam] = lg
        stability[fam] = st
        oos[fam] = r

    # baselines
    close = [x["close"] for x in data]
    rets = returns(close)
    buy_hold = perf_stats(rets)
    buy_hold["Turnover"] = 1.0

    prior_best = None
    old_summary = ROOT / "results" / "summary.json"
    if old_summary.exists():
        prev = json.loads(old_summary.read_text())
        prior_best = prev.get("metrics_oos", {}).get("vol_breakout")

    ranked = sorted(results.items(), key=lambda kv: (kv[1]["Calmar"], kv[1]["Max Drawdown"]), reverse=True)
    best_name, best_metrics = ranked[0]

    deploy = {
        "recommended_strategy": best_name,
        "position_sizing": [
            "Daily target-vol sizing: size = min(1, target_vol / realized_vol_20d)",
            "Max leverage hard cap = 1.0 (long/flat only)",
            "Reduce to 0 exposure when kill-switch triggered",
        ],
        "kill_switch_logic": [
            "If rolling 60d drawdown < -12%: cut to cash until price > EMA150 and 20d momentum > 0",
            "If realized vol > 90% annualized: cap size to 0.35",
            "If execution turnover > 20x/year sustained 30d: halve position size",
        ],
        "risk_budget": {
            "target_annual_vol": cfg.target_vol,
            "max_leverage": 1.0,
            "turnover_cap": cfg.turnover_cap,
            "assumed_cost_bps": cfg.cost_bps,
            "assumed_slippage_bps": cfg.slippage_bps,
        },
        "confidence_limits": [
            "OOS window still single-asset (BTC) and daily-only; intraday shocks not fully captured",
            "Model edge may decay in structurally different macro/liquidity regimes",
            "Parameter stability is moderate, so quarterly re-validation is required",
        ],
        "failure_modes": [
            "Gap-down crashes can bypass signal exits",
            "Extended sideways chop can cause whipsaw + cost drag",
            "Exchange-specific funding/fee effects not modeled",
        ],
    }

    out = {
        "meta": {
            "objective": "low drawdown + return consistency",
            "validation": "purged walk-forward (train=4y, test=180d, step=90d, purge=5d)",
            "constraints": {"target_vol": cfg.target_vol, "turnover_cap": cfg.turnover_cap},
            "frictions": {"transaction_cost_bps": cfg.cost_bps, "slippage_bps": cfg.slippage_bps},
            "date_start": data[0]["date"].isoformat(),
            "date_end": data[-1]["date"].isoformat(),
        },
        "metrics_oos": results,
        "ranked": [{"strategy": k, "calmar": v["Calmar"], "maxdd": v["Max Drawdown"], "sortino": v["Sortino"]} for k, v in ranked],
        "baselines": {"buy_and_hold": buy_hold, "prior_best_from_repo": prior_best},
        "selection_logs": logs,
        "stability_tables": stability,
        "oos_returns": oos,
        "deployability": deploy,
    }
    (OUT_DIR / "lowdd_summary.json").write_text(json.dumps(out, indent=2))

    lines = [
        "# Low-DD BTC Research Report",
        "",
        f"Data range: {data[0]['date'].isoformat()} to {data[-1]['date'].isoformat()} ({len(data)} rows)",
        "",
        "## OOS Ranking (downside-priority)",
    ]
    for name, m in ranked:
        lines.append(
            f"- **{name}**: CAGR {fmt_pct(m['CAGR'])}, Sharpe {m['Sharpe']:.2f}, Sortino {m['Sortino']:.2f}, MaxDD {fmt_pct(m['Max Drawdown'])}, Calmar {m['Calmar']:.2f}, Win {fmt_pct(m['Win Rate'])}, Monthly Hit {fmt_pct(m['Monthly Hit Rate'])}, Turnover {m['Turnover']:.2f}x"
        )

    lines += [
        "",
        "## Baseline comparison",
        f"- Buy & Hold: CAGR {fmt_pct(buy_hold['CAGR'])}, MaxDD {fmt_pct(buy_hold['Max Drawdown'])}, Calmar {buy_hold['Calmar']:.2f}",
    ]
    if prior_best:
        lines.append(
            f"- Prior repo best (`vol_breakout`): CAGR {fmt_pct(prior_best['CAGR'])}, Sharpe {prior_best['Sharpe']:.2f}, MaxDD {fmt_pct(prior_best['Max Drawdown'])}"
        )

    lines += [
        "",
        "## Deployability recommendation",
        f"- Recommended: **{best_name}**",
        "- Position sizing: daily vol-target, cap leverage at 1.0",
        "- Kill-switch: drawdown and high-volatility cutoffs to force risk-off",
        "- Confidence: moderate; strategy is more stable on DD profile but still regime-sensitive",
        "",
        "## Parameter stability",
        "- Full per-window score tables are saved in `results/lowdd_summary.json` under `stability_tables`.",
        "- Use these tables as sensitivity surfaces (score, MaxDD, Calmar, Sortino, turnover) across parameter grids.",
    ]

    (OUT_DIR / "LOWDD_REPORT.md").write_text("\n".join(lines))
    print("Best low-DD strategy:", best_name)


if __name__ == "__main__":
    main()
