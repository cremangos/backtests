"""Sweep breakeven_trigger and trail_distance combos to find the best
trailing-stop configuration per Mr. Zinc's actual rules.

Strategy:
- Entry: at 50% midpoint of IB, allowed from 10:30 (STRICT - no front-run)
- Target: opposite IB boundary (ibh_ibl)
- Stop: AT the formed boundary (bottom) -- the 1:1 R:R invalidation point
- Management: move to breakeven at +X pts, then trail Y pts behind

Grid:
  breakeven_trigger: 0, 20, 35, 50, 75, 100
  trail_distance:     0, 15, 25, 35, 50
Total: 6 * 5 = 30 configs (plus the X=0,Y=0 baseline = 1 unique, so 30).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")

from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.monte_carlo import run_monte_carlo
from ib_backtest.stats import compute_stats, stats_to_dict

NQ_MULT = 20.0
STARTING_EQUITY = 10_000.0
RISK_PER_TRADE = 200.0

BE_TRIGGERS = [0, 20, 35, 50, 75, 100]
TRAIL_DISTANCES = [0, 15, 25, 35, 50]


def main() -> None:
    path = "//192.168.2.40/proxmox-fileserver/profiler_data/nq-1m_bk.csv"
    print(f"Loading NQ from {path}...")
    df = load_csv(path)
    print(f"  {len(df):,} rows, {df.index[0]} -> {df.index[-1]}")
    df = df.loc["2024-06-01":"2026-06-01"]
    print(f"  Window: {len(df):,} rows")

    rows = []
    for be in BE_TRIGGERS:
        for tr in TRAIL_DISTANCES:
            # Skip configs where trail is set but BE trigger is 0 -- they wouldn't do anything.
            if tr > 0 and be == 0:
                continue
            cfg = BacktestConfig(
                ib_start="09:30",
                ib_end="10:30",
                session_end="16:00",
                min_entry_time="10:30",  # STRICT: wait for IB to finalize
                entry_type="midpoint_only",
                target_type="ibh_ibl",
                stop_basis="bottom",      # Mr. Zinc's actual rule: 1:1 R:R
                contract_multiplier=NQ_MULT,
                risk_per_trade=RISK_PER_TRADE,
                breakeven_trigger_pts=float(be),
                trail_distance_pts=float(tr),
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
            row["be_trigger"] = be
            row["trail_distance"] = tr
            row["ror_full"] = mc.ror_full
            row["ror_14day"] = mc.ror_14day
            rows.append(row)

    df_out = pd.DataFrame(rows)
    cols = [
        "be_trigger", "trail_distance", "total_trades", "win_rate", "profit_factor",
        "expectancy", "avg_pnl", "avg_win", "avg_loss", "avg_rr",
        "max_consecutive_losses", "max_dd_dollars", "doomsday_budget",
        "mae_p50", "mfe_p50", "mfe_capture_pct",
        "stopout_rate_mae_p30", "target_hit_rate_mfe_p30",
        "mae_mfe_sync_pass", "kelly_pct", "combined_edge",
        "ror_full", "ror_14day", "runtime_seconds",
    ]
    print("\n" + "=" * 200)
    print(f"  NQ 2024-06 to 2026-06 -- IB By Rejection (Mr. Zinc rules)")
    print(f"  Stop=formed boundary, breakeven+X pts, trail Y pts")
    print("=" * 200)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 250)
    print(df_out[cols].to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
    out = Path("results/trailing_sweep_nq.csv")
    df_out[cols].to_csv(out, index=False)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
