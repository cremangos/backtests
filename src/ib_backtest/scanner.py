"""Parameter sweep runner.

Tests all combinations of:
- Stop basis: ib75, ib50, ib25, bottom, points_50, points_100, points_150, points_200
- Entry type: midpoint_only, breakout_only, either
- Target type: ibh_ibl, ibh2_ibl2

Writes one results CSV per parameter set to the results/ directory.
"""
from __future__ import annotations

import itertools
import json
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .data import load_csv
from .engine import BacktestConfig, run_backtest
from .monte_carlo import run_monte_carlo
from .stats import compute_stats, stats_to_dict, trades_to_df

STOP_BASES = ["ib75", "ib50", "ib25", "bottom",
              "points_25", "points_50", "points_100", "points_150", "points_200"]
ENTRY_TYPES = ["midpoint_only", "breakout_only", "either"]
TARGET_TYPES = ["ibh_ibl", "ibh2_ibl2"]
NQ_MULTIPLIER = 20.0  # $/point for NQ E-mini
ES_MULTIPLIER = 50.0  # $/point for ES E-mini


def sweep(
    df: pd.DataFrame,
    symbol: str = "NQ",
    multiplier: float = NQ_MULTIPLIER,
    out_dir: str | Path = "results",
    starting_equity: float = 10_000.0,
    risk_per_trade: float = 200.0,
    n_simulations: int = 5_000,
    stop_bases: list[str] | None = None,
    entry_types: list[str] | None = None,
    target_types: list[str] | None = None,
) -> pd.DataFrame:
    """Run the full parameter sweep. Returns a DataFrame of summary metrics."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stop_bases = stop_bases or STOP_BASES
    entry_types = entry_types or ENTRY_TYPES
    target_types = target_types or TARGET_TYPES

    rows = []
    for stop, entry, target in itertools.product(stop_bases, entry_types, target_types):
        cfg = BacktestConfig(
            stop_basis=stop,
            entry_type=entry,
            target_type=target,
            contract_multiplier=multiplier,
            risk_per_trade=risk_per_trade,
        )
        t0 = time.time()
        result = run_backtest(df, cfg)
        runtime = time.time() - t0
        stats = compute_stats(result, runtime_seconds=runtime)
        mc = run_monte_carlo(
            result,
            starting_equity=starting_equity,
            risk_per_trade=risk_per_trade,
            n_simulations=n_simulations,
        )

        # Write per-set trade CSV
        trade_df = trades_to_df(result.trades)
        if len(trade_df) > 0:
            tag = f"{symbol.lower()}_{stop}_{entry}_{target}"
            trade_df.to_csv(out / f"trades_{tag}.csv", index=False)

        row = stats_to_dict(stats)
        row["symbol"] = symbol
        row["stop_basis"] = stop
        row["entry_type"] = entry
        row["target_type"] = target
        row["ror_full"] = mc.ror_full
        row["ror_14day"] = mc.ror_14day
        row["mc_median_max_dd"] = mc.median_max_dd
        row["mc_worst_max_dd"] = mc.worst_max_dd
        row["mc_median_final_equity"] = mc.median_final_equity
        row["mc_n_sims"] = mc.n_simulations
        rows.append(row)

    summary = pd.DataFrame(rows)
    summary_path = out / f"sweep_{symbol.lower()}_summary.csv"
    summary.to_csv(summary_path, index=False)
    return summary


def main() -> None:
    """CLI entry point. Reads NQ and ES from DATA_ROOT and runs the sweep."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    data_root = Path(os.environ.get("DATA_ROOT", r"\\192.168.2.40\proxmox-fileserver\profiler_data"))
    starting_equity = float(os.environ.get("STARTING_EQUITY", "10000"))
    risk_per_trade = float(os.environ.get("RISK_PER_TRADE", "200"))

    nq_path = data_root / os.environ.get("NQ_CSV", "nq-1m_bk.csv")
    es_path = data_root / os.environ.get("ES_CSV", "es-1m_bk.csv")

    print(f"Loading NQ from {nq_path}...")
    nq = load_csv(nq_path)
    print(f"  {len(nq):,} rows, {nq.index[0]} -> {nq.index[-1]}")
    print("Running NQ sweep...")
    nq_summary = sweep(nq, symbol="NQ", multiplier=NQ_MULTIPLIER,
                       starting_equity=starting_equity, risk_per_trade=risk_per_trade)
    print(f"  NQ sweep done: {len(nq_summary)} parameter sets")
    print(nq_summary[["stop_basis", "entry_type", "target_type",
                       "total_trades", "win_rate", "profit_factor",
                       "expectancy", "max_consecutive_losses",
                       "ror_full", "ror_14day"]].head(20).to_string(index=False))

    print(f"\nLoading ES from {es_path}...")
    es = load_csv(es_path)
    print(f"  {len(es):,} rows, {es.index[0]} -> {es.index[-1]}")
    print("Running ES sweep...")
    es_summary = sweep(es, symbol="ES", multiplier=ES_MULTIPLIER,
                       starting_equity=starting_equity, risk_per_trade=risk_per_trade)
    print(f"  ES sweep done: {len(es_summary)} parameter sets")
    print(es_summary[["stop_basis", "entry_type", "target_type",
                       "total_trades", "win_rate", "profit_factor",
                       "expectancy", "max_consecutive_losses",
                       "ror_full", "ror_14day"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
