"""Full sweep of the simple IB By Rejection strategy across all stop bases.

Strategy:
- Entry: at 50% of IB (midpoint), allowed from 10:23 (front-run)
- Target: opposite IB boundary (ibh_ibl)
- Stop: varies per config
- Exit: stop, target, or 4PM
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.monte_carlo import run_monte_carlo
from ib_backtest.stats import compute_stats, stats_to_dict

STOP_BASES = [
    "bottom",        # stop at the formed boundary (no buffer)
    "ib10",          # 10% buffer past boundary
    "ib25",          # 25% buffer
    "ib50",          # 50% buffer
    "ib75",          # 75% buffer
    "points_25",     # fixed 25-pt stop
    "points_50",
    "points_100",
    "points_150",
    "points_200",
]

NQ_MULT = 20.0
STARTING_EQUITY = 10_000.0
RISK_PER_TRADE = 200.0


def main() -> None:
    path = "//192.168.2.40/proxmox-fileserver/profiler_data/nq-1m_bk.csv"
    print(f"Loading NQ from {path}...")
    df = load_csv(path)
    print(f"  {len(df):,} rows, {df.index[0]} -> {df.index[-1]}")
    df = df.loc["2024-06-01":"2026-06-01"]
    print(f"  Window: {len(df):,} rows")

    rows = []
    for stop in STOP_BASES:
        cfg = BacktestConfig(
            ib_start="09:30",
            ib_end="10:30",
            session_end="16:00",
            min_entry_time="10:23",
            entry_type="midpoint_only",
            target_type="ibh_ibl",
            stop_basis=stop,
            contract_multiplier=NQ_MULT,
            risk_per_trade=RISK_PER_TRADE,
        )
        t0 = time.time()
        result = run_backtest(df, cfg)
        runtime = time.time() - t0
        stats = compute_stats(result, runtime_seconds=runtime)
        mc = run_monte_carlo(
            result,
            starting_equity=STARTING_EQUITY,
            risk_per_trade=RISK_PER_TRADE,
            n_simulations=2000,
        )
        row = stats_to_dict(stats)
        row["stop_basis"] = stop
        row["ror_full"] = mc.ror_full
        row["ror_14day"] = mc.ror_14day
        rows.append(row)

    df_out = pd.DataFrame(rows)
    cols = [
        "stop_basis", "total_trades", "win_rate", "profit_factor",
        "expectancy", "avg_pnl", "avg_win", "avg_loss", "avg_rr",
        "max_consecutive_losses", "max_dd_dollars", "doomsday_budget",
        "mae_p10", "mae_p30", "mae_p50", "mae_p70", "mae_mean",
        "mfe_p10", "mfe_p30", "mfe_p50", "mfe_p70", "mfe_mean",
        "stopout_rate_mae_p30", "stopout_rate_mae_p50",
        "target_hit_rate_mfe_p30", "target_hit_rate_mfe_p50",
        "mfe_capture_pct", "mae_capture_pct",
        "mae_mfe_sync_pass", "kelly_pct", "combined_edge",
        "ror_full", "ror_14day", "runtime_seconds",
    ]
    print("\n" + "=" * 200)
    print(f"  NQ 2024-06 to 2026-06 -- simple strategy: 10:23 entry, 50% midpoint, target=opp boundary, 4PM exit")
    print("  All Wolf framework metrics: MAE/MFE percentiles, stopout rates, target hit rates, Kelly, combined edge")
    print("=" * 200)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 250)
    print(df_out[cols].to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
    out = Path("results/simple_sweep_nq.csv")
    df_out[cols].to_csv(out, index=False)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
