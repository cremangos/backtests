"""Compare the strategy with and without require_test_before_entry."""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.stats import compute_stats, stats_to_dict

DATA = Path(r"\\192.168.2.40\proxmox-fileserver\profiler_data\nq-1m_bk.csv")
print("Loading NQ...")
df = load_csv(DATA)
print(f"  {len(df):,} rows")

# Last 6 months for quick comparison
df = df.loc["2026-01-01":"2026-06-01"]
print(f"  Window: {len(df):,} rows")

base_kwargs = dict(
    stop_basis="ib25",
    entry_type="midpoint_only",
    target_type="ibh2_ibl2",
    contract_multiplier=20.0,
)

scenarios = [
    ("baseline (no test)", BacktestConfig(**base_kwargs)),
    ("require_test=True", BacktestConfig(**base_kwargs, require_test=True)),
    ("require_test + hold_overnight", BacktestConfig(**base_kwargs, require_test=True, hold_overnight=True)),
    ("hold_overnight only", BacktestConfig(**base_kwargs, hold_overnight=True)),
]

for name, cfg in scenarios:
    t0 = time.time()
    result = run_backtest(df, cfg)
    stats = compute_stats(result, runtime_seconds=time.time() - t0)
    s = stats_to_dict(stats)
    print(f"\n{name}:")
    print(f"  Trades: {s['total_trades']} | Win%: {s['win_rate']:.1%} | PF: {s['profit_factor']:.2f} | EV: ${s['expectancy']:.0f}")
    print(f"  AvgWin: ${s['avg_win']:.0f} | AvgLoss: ${s['avg_loss']:.0f} | AvgRR: {s['avg_rr']:.2f}")
    print(f"  MaxConsLoss: {s['max_consecutive_losses']} | MaxDD: ${s['max_dd_dollars']:,.0f} | Doomsday: ${s['doomsday_budget']:,.0f}")
    print(f"  MAE mean/p50: {s['mae_mean']:.1f}/{s['mae_p50']:.1f} | MFE mean/p50: {s['mfe_mean']:.1f}/{s['mfe_p50']:.1f}")
