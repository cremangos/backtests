"""Run the full parameter sweep on NQ and ES data."""
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

from ib_backtest.data import load_csv
from ib_backtest.scanner import sweep, NQ_MULTIPLIER, ES_MULTIPLIER

DATA_ROOT = Path(r"\\192.168.2.40\proxmox-fileserver\profiler_data")

STARTING_EQUITY = 10_000.0
RISK_PER_TRADE = 200.0
N_SIMS = 2000

# Quick subset for first verification
# YEARS = slice("2023-01-01", "2025-12-31")  # 3-year window

print("=" * 80)
print("NQ FULL SWEEP")
print("=" * 80)
print(f"Loading NQ from {DATA_ROOT / 'nq-1m_bk.csv'}...")
t0 = time.time()
nq = load_csv(DATA_ROOT / "nq-1m_bk.csv")
print(f"  Loaded {len(nq):,} rows in {time.time()-t0:.1f}s")
print(f"  Range: {nq.index[0]} -> {nq.index[-1]}")

t0 = time.time()
nq_summary = sweep(
    nq, symbol="NQ", multiplier=NQ_MULTIPLIER,
    starting_equity=STARTING_EQUITY, risk_per_trade=RISK_PER_TRADE,
    n_simulations=N_SIMS,
)
print(f"NQ sweep done in {time.time()-t0:.1f}s -> {len(nq_summary)} parameter sets")

# Show top 10 by profit factor
print("\nTop 10 NQ parameter sets by Profit Factor:")
top = nq_summary.sort_values("profit_factor", ascending=False).head(10)
print(top[["stop_basis", "entry_type", "target_type",
            "total_trades", "win_rate", "profit_factor",
            "expectancy", "max_consecutive_losses",
            "ror_full", "ror_14day"]].to_string(index=False))

print("\n\nTop 10 NQ parameter sets by Expectancy (EV):")
top_ev = nq_summary.sort_values("expectancy", ascending=False).head(10)
print(top_ev[["stop_basis", "entry_type", "target_type",
               "total_trades", "win_rate", "profit_factor",
               "expectancy", "max_consecutive_losses",
               "ror_full", "ror_14day"]].to_string(index=False))

print("\n" + "=" * 80)
print("ES FULL SWEEP")
print("=" * 80)
print(f"Loading ES from {DATA_ROOT / 'es-1m_bk.csv'}...")
t0 = time.time()
es = load_csv(DATA_ROOT / "es-1m_bk.csv")
print(f"  Loaded {len(es):,} rows in {time.time()-t0:.1f}s")
print(f"  Range: {es.index[0]} -> {es.index[-1]}")

t0 = time.time()
es_summary = sweep(
    es, symbol="ES", multiplier=ES_MULTIPLIER,
    starting_equity=STARTING_EQUITY, risk_per_trade=RISK_PER_TRADE,
    n_simulations=N_SIMS,
)
print(f"ES sweep done in {time.time()-t0:.1f}s -> {len(es_summary)} parameter sets")

print("\nTop 10 ES parameter sets by Profit Factor:")
top = es_summary.sort_values("profit_factor", ascending=False).head(10)
print(top[["stop_basis", "entry_type", "target_type",
            "total_trades", "win_rate", "profit_factor",
            "expectancy", "max_consecutive_losses",
            "ror_full", "ror_14day"]].to_string(index=False))

print("\n\nTop 10 ES parameter sets by Expectancy:")
top_ev = es_summary.sort_values("expectancy", ascending=False).head(10)
print(top_ev[["stop_basis", "entry_type", "target_type",
               "total_trades", "win_rate", "profit_factor",
               "expectancy", "max_consecutive_losses",
               "ror_full", "ror_14day"]].to_string(index=False))
