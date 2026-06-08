"""Test the SIMPLE interpretation of IB By Rejection.

Per user: after IB forms (or front-run 10:23), enter at 50% (midpoint), target the high or low.
- No require_test filter
- No overnight holds
- target = opposite boundary (ibh_ibl), not 2x range
- stop = the formed-first boundary (bottom basis)
- Exit at 4PM or target/stop
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

END = pd.Timestamp("2026-06-01", tz="America/New_York")
START = END - pd.Timedelta(days=730)
STARTING_EQUITY = 10_000.0
RISK_PER_TRADE = 200.0
N_SIMS = 2000

print("Loading NQ...")
df = load_csv(DATA)
print(f"  {len(df):,} rows")
window_df = df.loc[START:END]
print(f"  Window: {len(window_df):,} rows")

# Per user: enter at 50% of IB, target high or low, exit at 4PM
# Variants: min_entry_time = 10:23 (front-run) or 10:30 (after IB close)
# Variants: target = ibh_ibl (just opposite boundary) - this is the spec
# Variants: stop = bottom (the formed-first boundary)

base = dict(
    stop_basis="bottom",   # the boundary that formed first is the invalidation
    entry_type="midpoint_only",
    target_type="ibh_ibl", # target = opposite boundary (NOT 2x)
    contract_multiplier=20.0,
    min_ib_range=5.0,
    require_test=False,
    hold_overnight=False,
    session_end="16:00",
)

scenarios = [
    ("Entry from 10:23 (front-run), target=opposite, stop=bottom", {**base, "min_entry_time": "10:23"}),
    ("Entry from 10:30 (after IB), target=opposite, stop=bottom",   {**base, "min_entry_time": "10:30"}),
    ("Entry from 10:23, target=opposite, stop=ib25 (small buffer)", {**base, "min_entry_time": "10:23", "stop_basis": "ib25"}),
    ("Entry from 10:30, target=opposite, stop=ib25",                {**base, "min_entry_time": "10:30", "stop_basis": "ib25"}),
    ("Entry from 10:23, target=2x range, stop=bottom",              {**base, "min_entry_time": "10:23", "target_type": "ibh2_ibl2"}),
    ("Entry from 10:23, target=2x range, stop=ib25",               {**base, "min_entry_time": "10:23", "target_type": "ibh2_ibl2", "stop_basis": "ib25"}),
]
scenarios = [(name, BacktestConfig(**kwargs)) for name, kwargs in scenarios]

print(f"\n{'Scenario':<60} {'Trades':>7} {'Win%':>7} {'PF':>6} {'EV':>8} {'AvgWin':>8} {'AvgLoss':>9} "
      f"{'AvgRR':>6} {'Cons':>5} {'MaxDD$':>9} {'Doom':>7} {'RoR%':>6} {'Time(s)':>7}")
print("-" * 165)

for name, cfg in scenarios:
    t0 = time.time()
    result = run_backtest(window_df, cfg)
    runtime = time.time() - t0
    stats = compute_stats(result, runtime_seconds=runtime)
    mc = run_monte_carlo(result, starting_equity=STARTING_EQUITY,
                         risk_per_trade=RISK_PER_TRADE, n_simulations=N_SIMS)
    s = stats_to_dict(stats)
    print(f"{name:<60} {s['total_trades']:>7} {s['win_rate']:>6.1%} {s['profit_factor']:>5.2f}x "
          f"${s['expectancy']:>6.0f} ${s['avg_win']:>6.0f} ${s['avg_loss']:>7.0f} "
          f"{s['avg_rr']:>5.2f} {s['max_consecutive_losses']:>5} ${s['max_dd_dollars']:>7,.0f} "
          f"${s['doomsday_budget']:>5,.0f} {mc.ror_full:>5.1%} {runtime:>6.1f}")
