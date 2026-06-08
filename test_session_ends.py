"""Compare session_end times: noon (12:00) vs 4PM (16:00).

With and without require_test. No overnight holds.
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.stats import compute_stats, stats_to_dict
from ib_backtest.monte_carlo import run_monte_carlo

DATA = Path(r"\\192.168.2.40\proxmox-fileserver\profiler_data\nq-1m_bk.csv")

# Past 2 years
END = pd.Timestamp("2026-06-01", tz="America/New_York")
START = END - pd.Timedelta(days=730)

STARTING_EQUITY = 10_000.0
RISK_PER_TRADE = 200.0
N_SIMS = 2000

print("Loading NQ...")
df = load_csv(DATA)
print(f"  {len(df):,} rows")
print(f"Filtering to {START.date()} -> {END.date()}...")
window_df = df.loc[START:END]
print(f"  {len(window_df):,} rows in window")

base = dict(
    stop_basis="ib25",
    entry_type="midpoint_only",
    target_type="ibh2_ibl2",
    contract_multiplier=20.0,
    min_ib_range=5.0,
    hold_overnight=False,  # we don't hold overnight
)

scenarios = [
    ("Noon exit, no test",   BacktestConfig(session_end="12:00", require_test=False, **base)),
    ("Noon exit, + test",    BacktestConfig(session_end="12:00", require_test=True, **base)),
    ("4PM exit, no test",    BacktestConfig(session_end="16:00", require_test=False, **base)),
    ("4PM exit, + test",     BacktestConfig(session_end="16:00", require_test=True, **base)),
]

print(f"\n{'Scenario':<28} {'Trades':>7} {'Win%':>7} {'PF':>6} {'EV':>8} {'AvgWin':>8} {'AvgLoss':>9} "
      f"{'AvgRR':>6} {'Cons':>5} {'MaxDD$':>9} {'Doom':>7} {'RoR%':>6} {'14d%':>6} {'Time(s)':>7}")
print("-" * 145)

for name, cfg in scenarios:
    t0 = time.time()
    result = run_backtest(window_df, cfg)
    runtime = time.time() - t0
    stats = compute_stats(result, runtime_seconds=runtime)
    mc = run_monte_carlo(result, starting_equity=STARTING_EQUITY,
                         risk_per_trade=RISK_PER_TRADE, n_simulations=N_SIMS)
    s = stats_to_dict(stats)
    print(f"{name:<28} {s['total_trades']:>7} {s['win_rate']:>6.1%} {s['profit_factor']:>5.2f}x "
          f"${s['expectancy']:>6.0f} ${s['avg_win']:>6.0f} ${s['avg_loss']:>7.0f} "
          f"{s['avg_rr']:>5.2f} {s['max_consecutive_losses']:>5} ${s['max_dd_dollars']:>7,.0f} "
          f"${s['doomsday_budget']:>5,.0f} {mc.ror_full:>5.1%} {mc.ror_14day:>5.1%} {runtime:>6.1f}")
