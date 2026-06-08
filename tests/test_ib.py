"""Smoke tests for the IB engine."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from ib_backtest.data import load_csv
from ib_backtest.ib import detect_ib
from ib_backtest.engine import BacktestConfig, run_backtest
from ib_backtest.stats import compute_stats


def _make_synthetic_day():
    """Build a small synthetic day: 9:30-16:00 ET, 1-min bars.

    IB: 9:30-10:30. Low forms first (bullish bias).
    Bar at idx 20 has low=99.0; bar at idx 40 has high=101.0.
    IB range = 2.0, midpoint = 100.0.
    After 10:30, price retraces to 100.0 (midpoint), then breaks above 101.0.
    """
    times = pd.date_range("2024-01-02 09:30", "2024-01-02 16:00", freq="1min", tz="America/New_York")
    n = len(times)
    close = np.full(n, 100.0, dtype=np.float64)
    open_ = np.full(n, 100.0, dtype=np.float64)
    high = np.full(n, 100.05, dtype=np.float64)
    low = np.full(n, 99.95, dtype=np.float64)

    # IB low bar at idx 20: low = 99.0
    open_[20] = 99.5
    high[20] = 99.7
    low[20] = 99.0
    close[20] = 99.5

    # IB high bar at idx 40: high = 101.0
    open_[40] = 100.5
    high[40] = 101.0
    low[40] = 100.4
    close[40] = 100.8

    # After IB, retracement to midpoint (100.0) around idx 80
    open_[80] = 99.9
    high[80] = 100.1
    low[80] = 99.8
    close[80] = 100.0  # midpoint touch

    # Then breakout above 101.0 around idx 100
    open_[100] = 100.9
    high[100] = 101.5
    low[100] = 100.7
    close[100] = 101.2  # above IBH

    df = pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": 1000,
    }, index=times)
    df.index.name = "timestamp"
    return df


def test_detect_ib_bullish():
    df = _make_synthetic_day()
    ib = detect_ib(df, "09:30", "10:30")
    assert ib is not None
    assert ib.bias == "bullish"
    assert ib.ib_low == pytest.approx(99.0, abs=0.01)
    assert ib.ib_high == pytest.approx(101.0, abs=0.01)
    assert ib.midpoint == pytest.approx(100.0, abs=0.01)
    assert ib.target == ib.ib_high


def test_run_day_bullish_midpoint_entry():
    df = _make_synthetic_day()
    cfg = BacktestConfig(stop_basis="ib50", entry_type="midpoint_only", target_type="ibh_ibl", min_ib_range=0.0)
    result = run_backtest(df, cfg)
    assert result.total_trades == 1
    t = result.trades[0]
    assert t.direction == "long"
    # After midpoint entry, price eventually breaks above 101 -> hits target
    assert t.hit_target


def test_run_day_short_setup():
    """Bearish setup: high forms first, then low."""
    times = pd.date_range("2024-01-02 09:30", "2024-01-02 16:00", freq="1min", tz="America/New_York")
    n = len(times)
    close = np.full(n, 100.0, dtype=np.float64)
    open_ = np.full(n, 100.0, dtype=np.float64)
    high = np.full(n, 100.05, dtype=np.float64)
    low = np.full(n, 99.95, dtype=np.float64)

    # IB high at idx 20: high = 101.0
    open_[20] = 100.5
    high[20] = 101.0
    low[20] = 100.4
    close[20] = 100.8

    # IB low at idx 40: low = 99.0
    open_[40] = 99.5
    high[40] = 99.7
    low[40] = 99.0
    close[40] = 99.5

    # After IB, retracement up to midpoint (100.0) at idx 80
    open_[80] = 99.9
    high[80] = 100.1
    low[80] = 99.8
    close[80] = 100.0

    # Then breakdown below 99.0 at idx 100
    open_[100] = 99.1
    high[100] = 99.3
    low[100] = 98.7
    close[100] = 98.8

    df = pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": 1000,
    }, index=times)
    df.index.name = "timestamp"

    cfg = BacktestConfig(stop_basis="bottom", entry_type="midpoint_only", target_type="ibh_ibl", min_ib_range=0.0)
    result = run_backtest(df, cfg)
    assert result.total_trades == 1
    t = result.trades[0]
    assert t.direction == "short"


def test_stats_empty():
    from ib_backtest.engine import BacktestResult
    res = BacktestResult(config=BacktestConfig())
    stats = compute_stats(res)
    assert stats.total_trades == 0
    assert stats.profit_factor == 0.0
