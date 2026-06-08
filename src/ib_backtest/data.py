"""BacktestMarket CSV loader.

Format: `date;time;open;high;low;close;volume` (semicolon-separated, no header)
Date format: DD/MM/YYYY
Time format: HH:MM (24-hour, exchange local time = ET for US futures)
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

DTYPE = {
    "open": "float32",
    "high": "float32",
    "low": "float32",
    "close": "float32",
    "volume": "int32",
}
COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]


def load_csv(path: str | Path, tz: str = "America/New_York") -> pd.DataFrame:
    """Load a BacktestMarket CSV into a DataFrame indexed by tz-aware DatetimeIndex.

    Parameters
    ----------
    path : str | Path
        Path to the CSV file.
    tz : str
        Timezone to localize the naive exchange times to. Default: America/New_York.

    Returns
    -------
    pd.DataFrame
        Indexed by DatetimeIndex (tz-aware), columns: open, high, low, close, volume.
    """
    df = pd.read_csv(
        path,
        sep=";",
        header=None,
        names=COLUMNS,
        dtype=DTYPE,
        parse_dates=False,
    )
    # Build a single datetime column. BacktestMarket format is DD/MM/YYYY.
    # The recent portion of the file mixes DD/MM and MM/DD for May 2026; fall back
    # to dayfirst=True with format="mixed" so we accept either layout.
    raw = df["date"].astype(str) + " " + df["time"].astype(str)
    try:
        dt = pd.to_datetime(raw, format="%d/%m/%Y %H:%M")
    except ValueError:
        dt = pd.to_datetime(raw, format="mixed", dayfirst=True, errors="coerce")
        bad = dt.isna().sum()
        if bad:
            print(f"  WARNING: {bad} rows have unparseable dates — dropped")
        dt = dt.dropna()
    # The CSV mixes prior-evening globex and RTH. Localize naive times to ET.
    # We do NOT use `tz_localize` with ambiguous/missing flags because the
    # BacktestMarket data is already stored in local time; we just attach the tz.
    dt = dt.dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward")
    df = df.assign(timestamp=dt).drop(columns=["date", "time"]).set_index("timestamp")
    # BacktestMarket data may have out-of-order rows from DST transitions / globex
    # rollover; sort to make partial-slice indexing safe.
    df = df.sort_index()
    return df


def get_trading_days(df: pd.DataFrame) -> list[date]:
    """Return the unique trading dates present in the DataFrame (in ET)."""
    return sorted(set(df.index.date.tolist()))


def filter_rth(
    df: pd.DataFrame,
    start: str = "09:30",
    end: str = "16:00",
) -> pd.DataFrame:
    """Filter to US equity Regular Trading Hours. Times are interpreted in df's index tz."""
    start_t = pd.Timestamp(f"1970-01-01 {start}").time()
    end_t = pd.Timestamp(f"1970-01-01 {end}").time()
    mask = (df.index.time >= start_t) & (df.index.time < end_t)
    return df.loc[mask]


def split_by_day(df: pd.DataFrame) -> Iterable[tuple[date, pd.DataFrame]]:
    """Yield (trading_date, day_df) tuples. The day_df contains all bars for that date."""
    for d, group in df.groupby(df.index.date):
        yield d, group


def has_rth_data(df: pd.DataFrame, target_date: date, min_bars: int = 300) -> bool:
    """Check if a date has at least `min_bars` of RTH bars (9:30-16:00 ET).

    A full RTH day has 390 bars (6.5 hours of 1-min bars).
    Early-close holidays (1:00 PM close) have ~210 bars.
    A 1:00 PM close is the typical minimum for a "real" trading day.

    Days with < min_bars RTH bars are excluded from the backtest because:
    - Sundays/holidays have 0 bars (markets closed)
    - Days with data holes may have partial RTH and produce a misleading IB
    """
    day = df.loc[f"{target_date.isoformat()} 09:30":f"{target_date.isoformat()} 15:59"]
    return len(day) >= min_bars


def get_good_trading_days(df: pd.DataFrame, min_rth_bars: int = 300) -> list[date]:
    """Return dates that have at least `min_rth_bars` RTH bars.

    Useful for filtering out Sundays, holidays, and days with data holes
    before running a backtest.
    """
    good = []
    for d in get_trading_days(df):
        if has_rth_data(df, d, min_bars=min_rth_bars):
            good.append(d)
    return good
