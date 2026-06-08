"""Live IB By Rejection strategy.

Mirrors the backtest engine in real time. The class is broker-agnostic: it emits
signals, and an external executor (NinjaTrader bridge, IBKR API, Tradovate, etc.)
is responsible for actually placing orders.

Usage:

    from ib_backtest.live import IBByRejectionLive
    strat = IBByRejectionLive(stop_basis="ib50", entry_type="either",
                               target_type="ibh_ibl", on_signal=my_executor)
    for bar in live_bars:
        strat.on_bar(symbol="NQ", timestamp=bar.ts, o=bar.o, h=bar.h,
                     l=bar.l, c=bar.c, v=bar.v)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Callable, Literal

import pandas as pd

from .ib import InitialBalance, detect_ib
from .engine import _compute_target, _compute_stop, _touch_midpoint, _breakout

Signal = Literal["enter_long", "enter_short", "exit"]
STOP_MULTIPLIER = {"ib75": 0.75, "ib50": 0.50, "ib25": 0.25, "bottom": 0.0}


@dataclass
class SignalEvent:
    signal: Signal
    symbol: str
    timestamp: pd.Timestamp
    price: float
    stop: float
    target: float
    reason: str = ""


class IBByRejectionLive:
    """Stateful live strategy. Call on_bar() once per 1-minute bar."""

    def __init__(
        self,
        stop_basis: str = "ib50",
        entry_type: str = "either",
        target_type: str = "ibh_ibl",
        on_signal: Callable[[SignalEvent], None] | None = None,
        contract_multiplier: float = 20.0,
        risk_per_trade: float = 200.0,
        min_ib_range: float = 5.0,
    ) -> None:
        self.stop_basis = stop_basis
        self.entry_type = entry_type
        self.target_type = target_type
        self.on_signal = on_signal
        self.contract_multiplier = contract_multiplier
        self.risk_per_trade = risk_per_trade
        self.min_ib_range = min_ib_range

        # Per-day state
        self._current_date: date | None = None
        self._bars: list[tuple[pd.Timestamp, float, float, float, float, int]] = []
        self._ib: InitialBalance | None = None
        self._position: Literal["long", "short", None] = None
        self._entry_price: float | None = None
        self._entry_time: pd.Timestamp | None = None
        self._stop: float | None = None
        self._target: float | None = None

    def _emit(self, ev: SignalEvent) -> None:
        if self.on_signal is not None:
            self.on_signal(ev)

    def _reset_day(self) -> None:
        self._bars = []
        self._ib = None
        self._position = None
        self._entry_price = None
        self._entry_time = None
        self._stop = None
        self._target = None

    def on_bar(self, symbol: str, timestamp: pd.Timestamp,
               o: float, h: float, l: float, c: float, v: int) -> SignalEvent | None:
        """Process one new bar. Returns the SignalEvent emitted (if any)."""
        # Day roll-over
        bar_date = timestamp.date()
        if bar_date != self._current_date:
            self._reset_day()
            self._current_date = bar_date

        self._bars.append((timestamp, o, h, l, c, v))

        # Phase 1: collect IB until 10:30
        ib_end = time(10, 30)
        if timestamp.time() < ib_end:
            return None
        if self._ib is None:
            df = pd.DataFrame(self._bars, columns=["ts", "o", "h", "l", "c", "v"]).set_index("ts")
            ib = detect_ib(df, "09:30", "10:30")
            if ib is None or ib.range < self.min_ib_range:
                return None
            self._ib = ib

        # Session end - flatten any open position
        if timestamp.time() >= time(16, 0) and self._position is not None:
            ev = SignalEvent(
                signal="exit", symbol=symbol, timestamp=timestamp, price=c,
                stop=self._stop, target=self._target, reason="session_end",
            )
            self._emit(ev)
            self._position = None
            return ev

        # Phase 2: position management
        bar = {"open": o, "high": h, "low": l, "close": c}

        if self._position is None:
            # Look for entry
            assert self._ib is not None
            if self.entry_type in ("midpoint_only", "either") and _touch_midpoint(bar, self._ib):
                direction = "long" if self._ib.bias == "bullish" else "short"
                self._open_position(direction, c, timestamp, symbol)
                return self._last_signal
            if self.entry_type in ("breakout_only", "either") and _breakout(bar, self._ib):
                direction = "long" if self._ib.bias == "bullish" else "short"
                self._open_position(direction, c, timestamp, symbol)
                return self._last_signal
        else:
            # Check exits
            if self._stop is not None and self._target is not None:
                hit = self._check_exit(bar, self._position, self._stop, self._target)
                if hit is not None:
                    exit_price, hit_target, hit_stop = hit
                    ev = SignalEvent(
                        signal="exit", symbol=symbol, timestamp=timestamp, price=exit_price,
                        stop=self._stop, target=self._target,
                        reason="target" if hit_target else "stop",
                    )
                    self._emit(ev)
                    self._position = None
                    self._entry_price = None
                    return ev
        return None

    def _open_position(self, direction: str, price: float, ts: pd.Timestamp, symbol: str) -> None:
        assert self._ib is not None
        self._position = direction
        self._entry_price = price
        self._entry_time = ts
        self._target = _compute_target(self._ib, self.target_type)
        if self.stop_basis.startswith("points_"):
            n = float(self.stop_basis.split("_", 1)[1])
            if direction == "long":
                self._stop = price - n
            else:
                self._stop = price + n
        else:
            base_stop = _compute_stop(self._ib, self.stop_basis)
            self._stop = base_stop
        sig = "enter_long" if direction == "long" else "enter_short"
        ev = SignalEvent(signal=sig, symbol=symbol, timestamp=ts, price=price,
                         stop=self._stop, target=self._target,
                         reason="entry")
        self._last_signal = ev
        self._emit(ev)

    @staticmethod
    def _check_exit(bar: dict, direction: str, stop: float, target: float):
        if direction == "long":
            hit_stop = bar["low"] <= stop
            hit_target = bar["high"] >= target
            if hit_stop and hit_target:
                return stop, False, True
            if hit_stop:
                return stop, False, True
            if hit_target:
                return target, True, False
        else:
            hit_stop = bar["high"] >= stop
            hit_target = bar["low"] <= target
            if hit_stop and hit_target:
                return stop, False, True
            if hit_stop:
                return stop, False, True
            if hit_target:
                return target, True, False
        return None
