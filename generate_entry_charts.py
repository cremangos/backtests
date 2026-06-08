"""Generate per-day chart data for the past 2 years.

For each trade day, save:
- Previous day bars (last 3 hours of RTH for context)
- Current day bars (first 3 hours after 10:30 IB)
- IB levels (high, low, midpoint)
- Entry price/time
- Stop, target
- Exit price/time, P&L
- Outcome (win/loss/breakeven)

Output: results/chart_data.json (single file, all days in one)
"""
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")

from ib_backtest.data import load_csv, has_rth_data
from ib_backtest.engine import BacktestConfig, run_backtest, TradeResult
from ib_backtest.ib import detect_ib

DATA = Path("//192.168.2.40/proxmox-fileserver/profiler_data/nq-1m_bk.csv")
OUT = Path("results/chart_data.json")

# IB By Rejection config (Mr. Zinc rules, STRICT — no front-run):
# - Entry: 50% midpoint of IB, allowed from 10:30 (IB must be finalized first)
# - Target: opposite IB boundary (ibh_ibl)
# - Stop: AT the formed boundary (1:1 R:R invalidation point)
# - Management: move stop to breakeven at +75 pts in profit, then trail 15 pts behind
# - Exit: stop, target, breakeven/trail, or 4PM (no overnight)
#
# Why strict: 5.3% of trading days have a bias flip between 10:23 and 10:30
# (new IBH or IBL forms in the last few minutes of the window). On those days,
# front-running the early IB commits to a direction that the FINAL IB contradicts.
# Strict mode eliminates this inconsistency for cleaner data collection.
CFG = BacktestConfig(
    ib_start="09:30",
    ib_end="10:30",
    session_end="16:00",
    min_entry_time="10:30",       # STRICT: wait for IB to finalize
    stop_basis="bottom",          # Mr. Zinc's actual rule
    entry_type="midpoint_only",
    target_type="ibh_ibl",
    contract_multiplier=20.0,
    min_ib_range=5.0,
    breakeven_trigger_pts=75.0,   # lock in at +75 pts in profit
    trail_distance_pts=15.0,      # then trail 15 pts behind price
)

# Past 2 years (from the data range). The data ends ~2026-06-01.
END = pd.Timestamp("2026-06-01", tz="America/New_York")
START = END - pd.Timedelta(days=730)  # ~2 years


def serialize_bar(ts, o, h, l, c, v):
    return {
        "t": int(ts.timestamp()),
        "o": float(o), "h": float(h), "l": float(l), "c": float(c), "v": int(v),
    }


def serialize_trade(t: TradeResult) -> dict:
    return {
        "date": t.date.isoformat(),
        "direction": t.direction,
        "ib_high": t.ib_high,
        "ib_low": t.ib_low,
        "ib_range": t.ib_range,
        "ib_mid": (t.ib_high + t.ib_low) / 2,
        "bias": t.bias,
        "ib_low_time": int(t.ib_low_time.timestamp()) if t.ib_low_time is not None else None,
        "ib_high_time": int(t.ib_high_time.timestamp()) if t.ib_high_time is not None else None,
        "entry_price": t.entry_price,
        "entry_time": int(t.entry_time.timestamp()),
        "stop_price": t.stop_price,
        "target_price": t.target_price,
        "exit_price": t.exit_price,
        "exit_time": int(t.exit_time.timestamp()),
        "pnl": t.pnl,
        "mae": t.mae,
        "mfe": t.mfe,
        "hit_target": t.hit_target,
        "hit_stop": t.hit_stop,
        "session_end": t.session_end,
        "entered_at_midpoint": t.entered_at_midpoint,
        "entered_at_breakout": t.entered_at_breakout,
    }


def get_window_bars(df: pd.DataFrame, target_date: date, hours: int = 3, exit_time: pd.Timestamp | None = None) -> list[dict]:
    """Return 1-min bars from `target_date` 09:30 to (09:30 + `hours`), extended to cover `exit_time` if given."""
    start_ts = pd.Timestamp(target_date, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
    end_ts = start_ts + pd.Timedelta(hours=hours)
    if exit_time is not None and exit_time > end_ts:
        end_ts = exit_time
    # Include the end bar; use a half-open interval.
    window = df.loc[start_ts:end_ts]
    if not window.index.is_monotonic_increasing:
        window = window.sort_index()
    return [serialize_bar(ts, row["open"], row["high"], row["low"], row["close"], row["volume"])
            for ts, row in window.iterrows()]


def get_prev_day_bars(df: pd.DataFrame, target_date: date, include_overnight: bool = True) -> list[dict]:
    """Return bars from the previous futures session (NOT overlapping the trade day).

    A NQ futures day runs from 18:00 ET (globex open) to 17:00 ET the next day
    (with a 1-hour maintenance break 17:00-18:00). For a trade on `target_date`,
    the "previous day" for context is the futures session that ended at 17:00 ET
    on `target_date`. We return its RTH (09:30-16:00 ET) plus the globex overnight
    (18:00 prev day -> 09:29 current day) so the chart shows continuous action
    WITHOUT overlapping the trade day's RTH bars.
    """
    # Find the most recent date with any data.
    prev_date = target_date - pd.Timedelta(days=1)
    available_dates = set(df.index.date)
    target_ts = pd.Timestamp(target_date, tz="America/New_York")
    for _ in range(7):
        if prev_date in available_dates:
            if include_overnight:
                # Previous futures day: 18:00 prev day -> 09:29 target_date
                # (must end BEFORE the trade day RTH to avoid overlap with day_bars)
                start_ts = pd.Timestamp(prev_date, tz="America/New_York") + pd.Timedelta(hours=18)
                end_ts = target_ts + pd.Timedelta(hours=9, minutes=29)
            else:
                # Last 3 hours of RTH of prev day
                end_ts = pd.Timestamp(prev_date, tz="America/New_York") + pd.Timedelta(hours=16)
                start_ts = end_ts - pd.Timedelta(hours=3)
            window = df.loc[start_ts:end_ts]
            if len(window) > 0:
                # ALWAYS sort ascending — BacktestMarket CSV is not guaranteed sorted
                # (DST transitions, globex rollover, etc.), and lightweight-charts
                # requires strict ascending time.
                if not window.index.is_monotonic_increasing:
                    window = window.sort_index()
                return [serialize_bar(ts, row["open"], row["high"], row["low"], row["close"], row["volume"])
                        for ts, row in window.iterrows()]
        prev_date = prev_date - pd.Timedelta(days=1)
    return []


def main():
    print(f"Loading NQ from {DATA}...")
    t0 = time.time()
    df = load_csv(DATA)
    print(f"  Loaded {len(df):,} rows in {time.time()-t0:.1f}s")

    # Filter to 2-year window
    print(f"Filtering to {START.date()} -> {END.date()}...")
    window_df = df.loc[START:END]
    print(f"  {len(window_df):,} rows in window")

    # Data quality report
    all_days = sorted(set(window_df.index.date))
    good_days = [d for d in all_days if has_rth_data(window_df, d, min_bars=200)]
    bad_days = [d for d in all_days if not has_rth_data(window_df, d, min_bars=200)]
    print(f"Data quality: {len(good_days)}/{len(all_days)} days have >= 200 RTH bars (excluded: {len(bad_days)})")
    if bad_days and len(bad_days) <= 30:
        print(f"  Excluded dates: {[str(d) for d in bad_days[:30]]}")

    # Run the backtest
    print(f"Running backtest with config ({CFG.stop_basis} / {CFG.entry_type} / {CFG.target_type})...")
    t0 = time.time()
    result = run_backtest(window_df, CFG)
    print(f"  {result.total_trades} trades in {time.time()-t0:.1f}s")

    # Build per-day data
    days = []
    for trade in result.trades:
        td = trade.date
        if isinstance(td, str):
            td = date.fromisoformat(td)
        # Get full prev day (including overnight/globex) + 3 hours of trade day,
        # extended to cover the exit bar if it lies beyond the 3-hour window.
        prev_bars = get_prev_day_bars(df, td, include_overnight=True)
        day_bars = get_window_bars(df, td, hours=3, exit_time=trade.exit_time)
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
