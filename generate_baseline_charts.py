"""Generate a baseline chart data file (no require_test, no hold_overnight) for A/B comparison."""
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from ib_backtest.data import load_csv
from ib_backtest.engine import BacktestConfig, run_backtest

DATA = Path(r"\\192.168.2.40\proxmox-fileserver\profiler_data\nq-1m_bk.csv")
OUT = Path("results/chart_data_baseline.json")

CFG = BacktestConfig(
    stop_basis="ib25",
    entry_type="midpoint_only",
    target_type="ibh2_ibl2",
    contract_multiplier=20.0,
    min_ib_range=5.0,
    # No require_test, no hold_overnight - matches the original chart data
)

END = pd.Timestamp("2026-06-01", tz="America/New_York")
START = END - pd.Timedelta(days=730)


def serialize_bar(ts, o, h, l, c, v):
    return {
        "t": int(ts.timestamp()),
        "o": float(o), "h": float(h), "l": float(l), "c": float(c), "v": int(v),
    }


def serialize_trade(t):
    return {
        "date": t.date.isoformat(),
        "direction": t.direction,
        "ib_high": t.ib_high, "ib_low": t.ib_low, "ib_range": t.ib_range,
        "ib_mid": (t.ib_high + t.ib_low) / 2,
        "bias": t.bias,
        "entry_price": t.entry_price, "entry_time": int(t.entry_time.timestamp()),
        "stop_price": t.stop_price, "target_price": t.target_price,
        "exit_price": t.exit_price, "exit_time": int(t.exit_time.timestamp()),
        "pnl": t.pnl, "mae": t.mae, "mfe": t.mfe,
        "hit_target": t.hit_target, "hit_stop": t.hit_stop,
        "session_end": t.session_end,
        "entered_at_midpoint": t.entered_at_midpoint,
        "entered_at_breakout": t.entered_at_breakout,
    }


def get_window_bars(df, target_date, hours=3):
    start_ts = pd.Timestamp(target_date, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
    end_ts = start_ts + pd.Timedelta(hours=hours)
    window = df.loc[start_ts:end_ts]
    return [serialize_bar(ts, row["open"], row["high"], row["low"], row["close"], row["volume"])
            for ts, row in window.iterrows()]


def get_prev_day_bars(df, target_date):
    prev_date = target_date - pd.Timedelta(days=1)
    available_dates = set(df.index.date)
    for _ in range(7):
        if prev_date in available_dates:
            start_ts = pd.Timestamp(prev_date, tz="America/New_York")
            end_ts = start_ts + pd.Timedelta(hours=23, minutes=59)
            window = df.loc[start_ts:end_ts]
            if len(window) > 0:
                return [serialize_bar(ts, row["open"], row["high"], row["low"], row["close"], row["volume"])
                        for ts, row in window.iterrows()]
        prev_date = prev_date - pd.Timedelta(days=1)
    return []


def main():
    print(f"Loading NQ from {DATA}...")
    df = load_csv(DATA)
    print(f"  {len(df):,} rows")

    window_df = df.loc[START:END]
    print(f"Filtering to {START.date()} -> {END.date()}...")
    print(f"  {len(window_df):,} rows in window")

    print("Running BASELINE backtest (no filters)...")
    t0 = time.time()
    result = run_backtest(window_df, CFG)
    print(f"  {result.total_trades} trades in {time.time()-t0:.1f}s")

    days = []
    for trade in result.trades:
        td = trade.date
        if isinstance(td, str):
            td = pd.Timestamp(td).date()
        prev_bars = get_prev_day_bars(df, td)
        day_bars = get_window_bars(df, td, hours=3)
        days.append({
            "trade": serialize_trade(trade),
            "prev_day_bars": prev_bars,
            "day_bars": day_bars,
        })

    payload = {
        "config": {
            "stop_basis": CFG.stop_basis,
            "entry_type": CFG.entry_type,
            "target_type": CFG.target_type,
            "require_test": CFG.require_test,
            "hold_overnight": CFG.hold_overnight,
        },
        "instrument": "NQ",
        "date_range": [str(START.date()), str(END.date())],
        "total_trades": result.total_trades,
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload))
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"Wrote {OUT} ({size_mb:.1f} MB) with {len(days)} trade days")


if __name__ == "__main__":
    main()
