"""IB By Rejection backtest engine with MAE/MFE tracking.

Entry logic (after IB window closes at 10:30 ET):
- midpoint_only: enter on a close that retraces into the IB range and touches the 50% level
- breakout_only: enter on a close that breaks the target boundary
- either:       enter on whichever signal fires first

Exit logic:
- Stop is hit on an intrabar touch (worst-case bar interpretation)
- Target is hit on an intrabar touch
- If both touched in the same bar, stop wins (conservative)
- If neither, close position at session end (16:00 ET) at the last bar's close
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, time
from typing import Literal

import numpy as np
import pandas as pd

from .ib import InitialBalance, detect_ib

EntryType = Literal["midpoint_only", "breakout_only", "either"]
TargetType = Literal["ibh_ibl", "ibh2_ibl2"]
StopBasis = Literal["ib75", "ib50", "ib25", "bottom"]  # plus points_<N> handled separately

# Map stop basis to multiplier on IB range beyond the boundary.
STOP_MULTIPLIER = {"ib10": 0.10, "ib25": 0.25, "ib50": 0.50, "ib75": 0.75, "bottom": 0.0}


@dataclass
class TradeResult:
    date: date
    direction: Literal["long", "short"]
    ib_high: float
    ib_low: float
    ib_range: float
    bias: str
    entry_price: float
    entry_time: pd.Timestamp
    stop_price: float
    target_price: float
    exit_price: float
    exit_time: pd.Timestamp
    pnl: float
    mae: float
    mfe: float
    hit_target: bool
    hit_stop: bool
    session_end: bool
    entered_at_midpoint: bool
    entered_at_breakout: bool
    stop_basis: str
    entry_type: str
    target_type: str
    risk: float             # dollar risk = abs(entry - stop) * multiplier
    stop_distance: float    # point distance from entry to stop
    reward_distance: float  # point distance from entry to target
    contract_multiplier: float  # $/point for the instrument
    ib_low_time: pd.Timestamp  # when IBL was first reached during 09:30-10:30 window
    ib_high_time: pd.Timestamp  # when IBH was first reached during 09:30-10:30 window

    def to_dict(self) -> dict:
        d = asdict(self)
        # Convert timestamps to ISO strings for CSV friendliness.
        d["entry_time"] = self.entry_time.isoformat()
        d["exit_time"] = self.exit_time.isoformat()
        d["date"] = self.date.isoformat()
        d["ib_low_time"] = self.ib_low_time.isoformat() if self.ib_low_time is not None else None
        d["ib_high_time"] = self.ib_high_time.isoformat() if self.ib_high_time is not None else None
        return d


@dataclass
class BacktestConfig:
    ib_start: str = "09:30"
    ib_end: str = "10:30"
    min_entry_time: str = "10:30"  # earliest bar to allow entry (default = IB close; STRICT mode)
    session_end: str = "16:00"
    entry_type: EntryType = "either"
    target_type: TargetType = "ibh_ibl"
    stop_basis: str = "ib50"  # or "bottom" / "ib75" / "ib25" / "points_50" etc.
    contract_multiplier: float = 20.0  # NQ: $20/pt; ES: $50/pt
    risk_per_trade: float = 200.0  # used for risk_$ on trade record
    min_ib_range: float = 5.0  # skip days with tiny IB (< 5 pts on NQ)
    max_ib_range: float = 0.0  # 0 = no cap
    require_test: bool = False  # require target boundary to be tested before entry
    hold_overnight: bool = False  # hold past session_end until next day or target/stop hit
    max_hold_bars: int = 0  # 0 = no limit; else force exit after N bars in trade
    min_rth_bars: int = 200  # skip days with < N RTH bars (data quality: excludes Sundays, partial-data days)
    # Trailing stop management (Mr. Zinc's actual rules)
    breakeven_trigger_pts: float = 0.0  # once price is X pts in profit, move stop to entry (0 = off)
    trail_distance_pts: float = 0.0  # once breakeven triggered, trail stop X pts behind price (0 = off)


@dataclass
class BacktestResult:
    config: BacktestConfig
    trades: list[TradeResult] = field(default_factory=list)

    @property
    def total_trades(self) -> int:
        return len(self.trades)


def _compute_stop(ib: InitialBalance, basis: str) -> float:
    """Return the stop price for a trade based on the IB and stop basis string."""
    if basis in STOP_MULTIPLIER:
        m = STOP_MULTIPLIER[basis]
        if ib.bias == "bullish":
            return ib.ib_low - m * ib.range
        else:
            return ib.ib_high + m * ib.range
    if basis.startswith("points_"):
        n = float(basis.split("_", 1)[1])
        # Fixed-point stop: we apply it relative to the ENTRY (not the boundary).
        # The engine will adjust this after entry.
        return n
    raise ValueError(f"Unknown stop basis: {basis}")


def _compute_target(ib: InitialBalance, target_type: TargetType) -> float:
    if target_type == "ibh_ibl":
        return ib.target
    if target_type == "ibh2_ibl2":
        if ib.bias == "bullish":
            return ib.ib_high + ib.range
        else:
            return ib.ib_low - ib.range
    raise ValueError(f"Unknown target type: {target_type}")


def _touch_midpoint(bar: pd.Series, ib: InitialBalance) -> bool:
    """Did this bar's high/low straddle the IB midpoint?"""
    return bar["low"] <= ib.midpoint <= bar["high"]


def _breakout(bar: pd.Series, ib: InitialBalance) -> bool:
    """Did this bar's close break the target boundary in the bias direction?"""
    if ib.bias == "bullish":
        return bar["close"] > ib.ib_high
    return bar["close"] < ib.ib_low


def _check_exit(bar: pd.Series, direction: str, stop: float, target: float) -> tuple[float | None, bool, bool]:
    """Check if the bar hits stop or target. Stop wins on tie (conservative).

    Returns (exit_price, hit_target, hit_stop). exit_price is None if no exit.
    """
    if direction == "long":
        hit_stop = bar["low"] <= stop
        hit_target = bar["high"] >= target
        if hit_stop and hit_target:
            return stop, False, True
        if hit_stop:
            return stop, False, True
        if hit_target:
            return target, True, False
        return None, False, False
    else:  # short
        hit_stop = bar["high"] >= stop
        hit_target = bar["low"] <= target
        if hit_stop and hit_target:
            return stop, False, True
        if hit_stop:
            return stop, False, True
        if hit_target:
            return target, True, False
        return None, False, False


def run_day(day_df: pd.DataFrame, cfg: BacktestConfig) -> TradeResult | None:
    """Run the IB By Rejection strategy on a single trading day.

    Returns a TradeResult or None if no trade was taken.
    """
    # Data quality: skip days with insufficient RTH bars (data holes, partial sessions).
    # A full RTH day is 390 bars; a 1:00 PM early close is ~210 bars. We set
    # cfg.min_rth_bars=200 to keep legitimate 1pm-close holidays (210+ bars)
    # while excluding data-hole days that show only 150 bars or less.
    rth = day_df.between_time("09:30", "15:59")
    if len(rth) < cfg.min_rth_bars:
        return None

    ib = detect_ib(day_df, ib_start=cfg.ib_start, ib_end=cfg.ib_end)
    if ib is None:
        return None
    if ib.range < cfg.min_ib_range:
        return None
    if cfg.max_ib_range > 0 and ib.range > cfg.max_ib_range:
        return None

    # Filter to entry-eligible bars (default: after IB close, but can be earlier to front-run).
    ib_end_t = pd.Timestamp(f"1970-01-01 {cfg.ib_end}").time()
    min_entry_t = pd.Timestamp(f"1970-01-01 {cfg.min_entry_time}").time()
    session_end_t = pd.Timestamp(f"1970-01-01 {cfg.session_end}").time()
    post = day_df.loc[day_df.index.time >= min_entry_t]
    post = post.loc[post.index.time < session_end_t]
    if len(post) == 0:
        return None

    target = _compute_target(ib, cfg.target_type)
    base_stop = _compute_stop(ib, cfg.stop_basis)

    # Determine which boundary is the "target side" being aimed for.
    # For bullish bias: target = IBH (we want price to break above).
    # For bearish bias: target = IBL (we want price to break below).
    target_boundary = ib.ib_high if ib.bias == "bullish" else ib.ib_low

    def _target_breached(bar: pd.Series) -> bool:
        """Did this bar CLOSE through the target boundary (invalidates the setup)?"""
        if ib.bias == "bullish":
            return bar["close"] > ib.ib_high
        return bar["close"] < ib.ib_low

    def _stop_touched(bar: pd.Series) -> bool:
        """Did this bar's high/low trade AT or past the stop boundary?

        The stop is at the formed boundary (IBH for shorts, IBL for longs).
        If price traded at that level before we entered, our stop would have
        triggered, so the rejection setup is dead -- skip the trade.

        We use 'touched' (high/low), not 'closed through', because Mr. Zinc's
        rule is a 1-tick stop: any wick that hits the boundary is a stop-out.
        """
        if ib.bias == "bullish":  # long: stop at IBL
            return bar["low"] <= ib.ib_low
        return bar["high"] >= ib.ib_high  # short: stop at IBH

    entry_price = entry_time = None
    entered_at_midpoint = entered_at_breakout = False
    direction = "long" if ib.bias == "bullish" else "short"
    test_confirmed = not cfg.require_test  # if no test required, always confirmed
    bars_in_trade = 0

    for ts, bar in post.iterrows():
        if entry_price is None:
            # If the target boundary has been closed through BEFORE we ever
            # touched the midpoint, the IB rejection setup is gone -- skip the day.
            if _target_breached(bar):
                return None
            # If the stop boundary has been traded at BEFORE we ever entered,
            # the rejection setup is dead -- our stop would have already triggered.
            # E.g., for a SHORT, if any bar's high >= IBH before entry, the bearish
            # thesis is gone (price already showed acceptance above the high).
            if _stop_touched(bar):
                return None
            # Track whether the target boundary has been tested (for confirmation).
            if cfg.require_test and not test_confirmed:
                if ib.bias == "bullish":
                    # For long, we want IBL to be tested (low touches IBL).
                    if bar["low"] <= ib.ib_low:
                        test_confirmed = True
                else:
                    # For short, we want IBH to be tested (high touches IBH).
                    if bar["high"] >= ib.ib_high:
                        test_confirmed = True
            if not test_confirmed:
                continue
            if cfg.entry_type in ("midpoint_only", "either") and _touch_midpoint(bar, ib):
                entry_price = float(bar["close"])
                entry_time = ts
                entered_at_midpoint = True
            elif cfg.entry_type in ("breakout_only", "either") and _breakout(bar, ib):
                entry_price = float(bar["close"])
                entry_time = ts
                entered_at_breakout = True
            else:
                continue
        # We are in a position from this bar onward.
        # Determine the stop for this trade.
        if cfg.stop_basis.startswith("points_"):
            n = float(cfg.stop_basis.split("_", 1)[1])
            if direction == "long":
                stop = entry_price - n
            else:
                stop = entry_price + n
        else:
            stop = base_stop

        # Initialize MAE/MFE on entry bar (high/low relative to entry).
        if direction == "long":
            mfe = max(0.0, float(bar["high"]) - entry_price)
            mae = max(0.0, entry_price - float(bar["low"]))
        else:
            mfe = max(0.0, entry_price - float(bar["low"]))
            mae = max(0.0, float(bar["high"]) - entry_price)

        # Walk remaining bars of the day to update MAE/MFE and check exits.
        # Note: 'bar' is the ENTRY bar; we need subsequent bars.
        # If hold_overnight is True, walk the full day_df (including evening globex).
        if cfg.hold_overnight:
            post_entry = day_df.loc[day_df.index >= ts]
        else:
            post_entry = post.loc[post.index >= ts]
        exit_price = exit_time = None
        hit_target_flag = hit_stop_flag = session_end_flag = False

        for ts2, bar2 in post_entry.iterrows():
            if ts2 == ts and not cfg.hold_overnight:
                # Entry bar: already initialized MAE/MFE; just check exit.
                ep, ht, hs = _check_exit(bar2, direction, stop, target)
                if ep is not None:
                    exit_price, exit_time, hit_target_flag, hit_stop_flag = ep, ts2, ht, hs
                    break
                continue
            # Update MAE/MFE
            if direction == "long":
                mfe = max(mfe, float(bar2["high"]) - entry_price)
                mae = max(mae, entry_price - float(bar2["low"]))
            else:
                mfe = max(mfe, entry_price - float(bar2["low"]))
                mae = max(mae, float(bar2["high"]) - entry_price)
            # Trailing-stop management: once we're breakeven_trigger points in profit,
            # move stop to entry (breakeven). Then trail stop_distance points behind
            # the current MFE. This matches Mr. Zinc's rule: lock at BE, then trail.
            # IMPORTANT: never tighten the stop past the target -- if target is hit on
            # the same bar as a tightened stop, the trade should still exit at target.
            if cfg.breakeven_trigger_pts > 0:
                if direction == "long" and mfe >= cfg.breakeven_trigger_pts:
                    be_stop = max(stop, entry_price)  # never loosen the stop
                    if cfg.trail_distance_pts > 0:
                        trailed = float(bar2["high"]) - cfg.trail_distance_pts
                        be_stop = max(be_stop, trailed)
                    be_stop = min(be_stop, target)  # never tighten past target
                    if be_stop > stop:
                        stop = be_stop
                elif direction == "short" and mfe >= cfg.breakeven_trigger_pts:
                    be_stop = min(stop, entry_price)
                    if cfg.trail_distance_pts > 0:
                        trailed = float(bar2["low"]) + cfg.trail_distance_pts
                        be_stop = min(be_stop, trailed)
                    be_stop = max(be_stop, target)  # never tighten past target
                    if be_stop < stop:
                        stop = be_stop
            # Check exit (now using possibly-tightened stop)
            ep, ht, hs = _check_exit(bar2, direction, stop, target)
            if ep is not None:
                exit_price, exit_time, hit_target_flag, hit_stop_flag = ep, ts2, ht, hs
                break
            # Force exit at session_end if not holding overnight
            if not cfg.hold_overnight and ts2.time() >= session_end_t:
                exit_price = float(bar2["close"])
                exit_time = ts2
                session_end_flag = True
                break
            # Cap hold bars
            bars_in_trade += 1
            if cfg.max_hold_bars > 0 and bars_in_trade >= cfg.max_hold_bars:
                exit_price = float(bar2["close"])
                exit_time = ts2
                session_end_flag = True
                break

        if exit_price is None:
            # Last bar of available data - close
            last_ts = post_entry.index[-1]
            last_bar = post_entry.iloc[-1]
            exit_price = float(last_bar["close"])
            exit_time = last_ts
            session_end_flag = True
            hit_target_flag = hit_stop_flag = False

        if direction == "long":
            pnl = (exit_price - entry_price) * cfg.contract_multiplier
        else:
            pnl = (entry_price - exit_price) * cfg.contract_multiplier

        risk_dollars = abs(entry_price - stop) * cfg.contract_multiplier
        stop_distance = abs(entry_price - stop)
        reward_distance = abs(target - entry_price)

        return TradeResult(
            date=day_df.index[0].date(),
            direction=direction,
            ib_high=ib.ib_high,
            ib_low=ib.ib_low,
            ib_range=ib.range,
            bias=ib.bias,
            entry_price=entry_price,
            entry_time=entry_time,
            stop_price=stop,
            target_price=target,
            exit_price=exit_price,
            exit_time=exit_time,
            pnl=pnl,
            mae=mae,
            mfe=mfe,
            hit_target=hit_target_flag,
            hit_stop=hit_stop_flag,
            session_end=session_end_flag,
            entered_at_midpoint=entered_at_midpoint,
            entered_at_breakout=entered_at_breakout,
            stop_basis=cfg.stop_basis,
            entry_type=cfg.entry_type,
            target_type=cfg.target_type,
            risk=risk_dollars,
            stop_distance=stop_distance,
            reward_distance=reward_distance,
            contract_multiplier=cfg.contract_multiplier,
            ib_low_time=ib.low_time,
            ib_high_time=ib.high_time,
        )

    return None


def run_backtest(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    """Run the IB By Rejection backtest on a multi-day DataFrame."""
    result = BacktestResult(config=cfg, trades=[])
    for d, day_df in df.groupby(df.index.date):
        trade = run_day(day_df, cfg)
        if trade is not None:
            result.trades.append(trade)
    return result
