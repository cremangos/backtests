"""Quick smoke test: load 2024 NQ data and run one backtest."""
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.stats import compute_stats, stats_to_dict

DATA = r"\\192.168.2.40\proxmox-fileserver\profiler_data\nq-1m_bk.csv"

print(f"Loading NQ from {DATA}...")
t0 = time.time()
df = load_csv(DATA)
print(f"  Loaded {len(df):,} rows in {time.time()-t0:.1f}s")
print(f"  Range: {df.index[0]} -> {df.index[-1]}")

# Filter to 2024 only for a quick test
print("Filtering to 2024...")
df_2024 = df.loc["2024-01-01":"2024-12-31"]
print(f"  2024 rows: {len(df_2024):,}")

# Run one backtest config
print("\nRunning backtest: ib50, midpoint_only, ibh_ibl...")
t0 = time.time()
cfg = BacktestConfig(stop_basis="ib50", entry_type="midpoint_only", target_type="ibh_ibl",
                     contract_multiplier=20.0)
result = run_backtest(df_2024, cfg)
runtime = time.time() - t0
stats = compute_stats(result, runtime_seconds=runtime)
print(f"  Total trades: {stats.total_trades}")
print(f"  Win rate: {stats.win_rate:.1%}")
print(f"  Profit factor: {stats.profit_factor:.2f}")
print(f"  Avg PnL: ${stats.avg_pnl:.2f}")
print(f"  Max DD: ${stats.max_dd_dollars:,.2f}")
print(f"  Max cons losses: {stats.max_consecutive_losses}")
print(f"  Runtime: {runtime:.1f}s")
print()
print("Full stats:")
for k, v in stats_to_dict(stats).items():
    print(f"  {k}: {v}")
