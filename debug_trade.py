"""Debug the 2024-06-03 SHORT trade."""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, "src")
from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.ib import detect_ib

DATA = Path(r"\\192.168.2.40\proxmox-fileserver\profiler_data\nq-1m_bk.csv")
print("Loading NQ...")
df = load_csv(DATA)
print(f"  {len(df):,} rows")

# Get the 2024-06-03 day
target = pd.Timestamp("2024-06-03", tz="America/New_York")
day_df = df.loc[target:target + pd.Timedelta(days=1)]
day_df = day_df[day_df.index.date == target.date()]
print(f"\nDay 2024-06-03: {len(day_df)} bars")
print(f"  Time range: {day_df.index[0].time()} -> {day_df.index[-1].time()}")

base = dict(stop_basis="ib25", entry_type="midpoint_only", target_type="ibh2_ibl2",
            min_ib_range=5.0, contract_multiplier=20.0)

scenarios = [
    ("baseline", BacktestConfig(**base)),
    ("require_test", BacktestConfig(**base, require_test=True)),
    ("require_test + hold_overnight", BacktestConfig(**base, require_test=True, hold_overnight=True)),
]

for name, cfg in scenarios:
    result = run_backtest(day_df, cfg)
    print(f"\n--- {name} ---")
    print(f"Trades: {result.total_trades}")
    for t in result.trades:
        print(f"  {t.date} {t.direction} bias={t.bias}")
        print(f"    IB: H={t.ib_high:.2f} L={t.ib_low:.2f} R={t.ib_range:.2f} mid={(t.ib_high+t.ib_low)/2:.2f}")
        print(f"    Entry: {t.entry_price:.2f} @ {t.entry_time}")
        print(f"    Stop: {t.stop_price:.2f}, Target: {t.target_price:.2f}")
        print(f"    Exit:  {t.exit_price:.2f} @ {t.exit_time}")
        print(f"    P&L: ${t.pnl:.2f}, MAE: {t.mae:.2f}, MFE: {t.mfe:.2f}")
        print(f"    hit_target={t.hit_target}, hit_stop={t.hit_stop}, session_end={t.session_end}")

