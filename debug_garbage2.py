"""Diagnose the 2024-06-03 garbage2.png trade.

Why did a SHORT @ 20073.48 with target=19997.27 (IBL) NOT hit target,
when the chart shows price clearly went below 19997 around 12:00?

Walk bar-by-bar from entry at 10:36 through 16:00 and print every bar
where low <= 19997.27 to see when the target was first reached.
"""
import sys
sys.path.insert(0, "src")

import pandas as pd

from ib_backtest.data import load_csv
from ib_backtest.ib import detect_ib

DATA = "//192.168.2.40/proxmox-fileserver/profiler_data/nq-1m_bk.csv"

print("Loading NQ...")
df = load_csv(DATA)
df = df.loc["2024-06-03":"2024-06-03"]
print(f"  {len(df)} rows on 2024-06-03")

ib = detect_ib(df)
print(f"  IB: high={ib.ib_high} low={ib.ib_low} range={ib.range:.2f} mid={ib.midpoint:.2f} bias={ib.bias}")
print(f"  IBL = {ib.ib_low}  (target for short)")

target = ib.ib_low  # 19997.27 for short
entry = 20073.48
entry_t = pd.Timestamp("2024-06-03 10:36:00", tz="America/New_York")

print(f"\nLooking for bars after entry @ {entry_t} where low <= {target}...")
post = df.loc[df.index >= entry_t]
print(f"  {len(post)} bars after entry")

hit_bars = []
for ts, bar in post.iterrows():
    if bar["low"] <= target:
        hit_bars.append((ts, bar["low"], bar["high"], bar["close"]))

if hit_bars:
    print(f"  FOUND {len(hit_bars)} bars where low <= target:")
    for ts, lo, hi, cl in hit_bars[:5]:
        print(f"    {ts}  low={lo:.2f}  high={hi:.2f}  close={cl:.2f}")
    if len(hit_bars) > 5:
        print(f"    ... and {len(hit_bars) - 5} more")
else:
    print("  NO BARS with low <= target found.")

# Also check if the engine has the entry bar at 10:36
print(f"\nEntry bar at 10:36:")
ten36 = df.loc[entry_t:entry_t]
print(ten36[["open", "high", "low", "close"]])
