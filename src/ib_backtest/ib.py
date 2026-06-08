"""Initial Balance (IB) detection.

IB window: 9:30:00 - 10:29:59 ET (first 60 minutes of RTH).
- IB High = max(high) in window
- IB Low = min(low) in window
- IB Range = IB High - IB Low
- IB Midpoint = (IB High + IB Low) / 2

Formation bias: which extreme formed first?
- Low forms first  -> bullish bias (target: IBH)
- High forms first -> bearish bias (target: IBL)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd

Bias = Literal["bullish", "bearish"]


@dataclass(frozen=True)
class InitialBalance:
    """The IB for a single trading day."""

    date: date
    ib_high: float
    ib_low: float
    range: float
    midpoint: float
    bias: Bias
    low_time: pd.Timestamp
    high_time: pd.Timestamp

    @property
    def target(self) -> float:
        """Opposite IB boundary from the bias."""
        return self.ib_high if self.bias == "bullish" else self.ib_low

    @property
    def stop_boundary(self) -> float:
        """The IB boundary being tested/used for the stop base."""
        return self.ib_low if self.bias == "bullish" else self.ib_high


def detect_ib(
    day_df: pd.DataFrame,
    ib_start: str = "09:30",
    ib_end: str = "10:30",
) -> InitialBalance | None:
    """Detect the Initial Balance from a single day's bars.

    Parameters
    ----------
    day_df : pd.DataFrame
        All bars for one trading date, indexed by tz-aware DatetimeIndex.
    ib_start, ib_end : str
        HH:MM strings defining the IB window. Default 09:30-10:30 (60 minutes).

    Returns
    -------
    InitialBalance | None
        None if there are not enough bars in the window.
    """
    start_t = pd.Timestamp(f"1970-01-01 {ib_start}").time()
    end_t = pd.Timestamp(f"1970-01-01 {ib_end}").time()
    mask = (day_df.index.time >= start_t) & (day_df.index.time < end_t)
    window = day_df.loc[mask]
    if len(window) < 5:
        return None

    ib_high = float(window["high"].max())
    ib_low = float(window["low"].min())
    # The time at which the IB high/low was first reached.
    high_time = window["high"].idxmax()
    low_time = window["low"].idxmin()

    bias: Bias = "bullish" if low_time < high_time else "bearish"

    return InitialBalance(
        date=day_df.index[0].date(),
        ib_high=ib_high,
        ib_low=ib_low,
        range=ib_high - ib_low,
        midpoint=(ib_high + ib_low) / 2,
        bias=bias,
        low_time=low_time,
        high_time=high_time,
    )
