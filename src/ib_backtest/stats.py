"""Aggregate TradeResult -> portfolio metrics (Wolf's framework).

Computes:
- Win rate, profit factor, expected value
- Max drawdown, max consecutive losses
- MAE/MFE percentiles and capture efficiency
- 14-day RoR placeholder (full RoR computed in monte_carlo.py)
- Doomsday budget = MaxDD / MaxConsecutiveLosses
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .engine import BacktestResult, TradeResult


@dataclass
class PortfolioStats:
    total_trades: int = 0
    winners: int = 0
    losers: int = 0
    win_rate: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    avg_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    max_drawdown: float = 0.0
    max_dd_dollars: float = 0.0
    max_consecutive_losses: int = 0
    doomsday_budget: float = 0.0
    mae_mean: float = 0.0
    mae_p10: float = 0.0
    mae_p30: float = 0.0
    mae_p50: float = 0.0
    mae_p70: float = 0.0
    mfe_mean: float = 0.0
    mfe_p10: float = 0.0
    mfe_p30: float = 0.0
    mfe_p50: float = 0.0
    mfe_p70: float = 0.0
    mfe_capture_pct: float = 0.0
    mae_capture_pct: float = 0.0
    avg_rr: float = 0.0
    # Wolf MFE/MAE framework: stopout rate at MAE percentiles
    # If you place your stop at MAE_p10, the stopout rate is 90% (because 90% of trades
    # have MAE >= the 10th percentile, i.e. price went that far against you).
    stopout_rate_mae_p10: float = 0.0  # expected 90% if MAE distribution is well-behaved
    stopout_rate_mae_p30: float = 0.0  # expected 70%
    stopout_rate_mae_p50: float = 0.0  # expected 50%
    stopout_rate_mae_p70: float = 0.0  # expected 30%
    # Wolf MFE/MAE framework: target hit rate at MFE percentiles
    # If you place your target at MFE_p30, the target hit rate is 70% (because 70% of trades
    # have MFE >= the 30th percentile, i.e. price reached that level).
    target_hit_rate_mfe_p10: float = 0.0  # expected 90%
    target_hit_rate_mfe_p30: float = 0.0  # expected 70%
    target_hit_rate_mfe_p50: float = 0.0  # expected 50%
    target_hit_rate_mfe_p70: float = 0.0  # expected 30%
    # MAE/MFE sync test (overfitting filter from the MAE/MFE doc)
    mae_mfe_sync_pass: bool = False
    # Kelly % and combined edge
    kelly_pct: float = 0.0
    combined_edge: float = 0.0  # expectancy × sqrt(win_rate)  (one common formulation)
    start_date: str = ""
    end_date: str = ""
    runtime_seconds: float = 0.0
    equity_curve: list[float] = field(default_factory=list)


def trades_to_df(trades: list[TradeResult]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    return pd.DataFrame([t.to_dict() for t in trades])


def compute_stats(result: BacktestResult, runtime_seconds: float = 0.0) -> PortfolioStats:
    """Compute portfolio statistics from a BacktestResult."""
    trades = result.trades
    if not trades:
        return PortfolioStats(runtime_seconds=runtime_seconds)

    # Pick up contract multiplier from the first trade (homogeneous per run).
    mult = trades[0].contract_multiplier

    df = trades_to_df(trades)
    pnl = df["pnl"].to_numpy()
    mae = df["mae"].to_numpy()
    mfe = df["mfe"].to_numpy()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    n = len(pnl)
    n_w = len(wins)
    n_l = len(losses)
    gross_profit = float(wins.sum()) if n_w else 0.0
    gross_loss = float(-losses.sum()) if n_l else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
    avg_win = float(wins.mean()) if n_w else 0.0
    avg_loss = float(losses.mean()) if n_l else 0.0
    avg_pnl = float(pnl.mean())
    win_rate = n_w / n if n else 0.0
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss

    # Equity curve & max drawdown
    equity = np.cumsum(pnl)
    running_max = np.maximum.accumulate(np.concatenate([[0.0], equity]))[1:]
    dd = running_max - equity
    max_dd_points = float(dd.max()) if len(dd) else 0.0
    # Dollar terms assume $20/pt (NQ) - the engine writes risk-adjusted pnl already.
    # We treat the curve itself as points and the largest valley as points.
    max_dd_dollars = max_dd_points  # pnl column is already in dollars

    # Max consecutive losses
    streak = 0
    max_streak = 0
    for p in pnl:
        if p < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    doomsday_budget = (max_dd_dollars / max_streak) if max_streak else 0.0

    # MAE / MFE percentiles
    def pctiles(arr: np.ndarray) -> dict[str, float]:
        if len(arr) == 0:
            return {"mean": 0.0, "p10": 0.0, "p30": 0.0, "p50": 0.0, "p70": 0.0}
        return {
            "mean": float(arr.mean()),
            "p10": float(np.percentile(arr, 10)),
            "p30": float(np.percentile(arr, 30)),
            "p50": float(np.percentile(arr, 50)),
            "p70": float(np.percentile(arr, 70)),
        }

    mae_stats = pctiles(mae)
    mfe_stats = pctiles(mfe)

    # Wolf MFE/MAE framework: stopout rate at each MAE percentile.
    # "If you place your stop at MAE_p10, what % of trades get stopped out?"
    # Answer: 100% - 10% = 90% (because only 10% of trades have MAE <= p10).
    def stopout_rate_at(p_value: float) -> float:
        # Count of trades where MAE >= p_value, divided by total
        if len(mae) == 0:
            return 0.0
        return float((mae >= p_value).sum() / len(mae))

    def hit_rate_at(arr: np.ndarray, p_value: float) -> float:
        if len(arr) == 0:
            return 0.0
        return float((arr >= p_value).sum() / len(arr))

    stopout_p10 = stopout_rate_at(mae_stats["p10"])  # expect ~0.90
    stopout_p30 = stopout_rate_at(mae_stats["p30"])  # expect ~0.70
    stopout_p50 = stopout_rate_at(mae_stats["p50"])  # expect ~0.50
    stopout_p70 = stopout_rate_at(mae_stats["p70"])  # expect ~0.30

    hit_mfe_p10 = hit_rate_at(mfe, mfe_stats["p10"])  # expect ~0.90
    hit_mfe_p30 = hit_rate_at(mfe, mfe_stats["p30"])  # expect ~0.70
    hit_mfe_p50 = hit_rate_at(mfe, mfe_stats["p50"])  # expect ~0.50
    hit_mfe_p70 = hit_rate_at(mfe, mfe_stats["p70"])  # expect ~0.30

    # MAE/MFE sync test: the overfitting filter from the MAE/MFE doc.
    # Pass if MFE_p50 > MAE_p50 (the average winner moves further than the average loser
    # is hurt) AND the stopout rate at MAE_p50 is close to 50% (matches the percentile).
    # A FAIL means the live price action isn't matching the backtest distribution.
    mae_mfe_sync_pass = bool(
        mfe_stats["p50"] > mae_stats["p50"]
        and 0.40 <= stopout_p50 <= 0.60
        and 0.40 <= hit_mfe_p50 <= 0.60
    )

    # Kelly %: f* = (b*p - q) / b  where b=avg_win/|avg_loss|, p=win_rate, q=1-p
    kelly = 0.0
    if avg_loss != 0:
        b = avg_win / abs(avg_loss)
        p = win_rate
        q = 1 - p
        kelly = max(0.0, (b * p - q) / b) if b > 0 else 0.0

    # Combined edge: one common formulation is EV * sqrt(win_rate).
    # Another is (win_rate * avg_win) / |avg_loss| - the "edge ratio".
    combined_edge = expectancy * (win_rate ** 0.5) if win_rate > 0 else 0.0

    # Capture efficiency: avg_win / avg_mfe (in points - convert avg_win from $)
    avg_mfe_points = mfe_stats["mean"]
    if avg_mfe_points > 0:
        avg_win_points = avg_win / mult
        mfe_capture_pct = avg_win_points / avg_mfe_points
    else:
        mfe_capture_pct = 0.0
    # MAE capture: avg_mae / avg_stop_distance (both in points)
    if "stop_distance" in df and len(df) > 0:
        mean_stop_dist = float(df["stop_distance"].mean())
        mae_capture_pct = (mae_stats["mean"] / mean_stop_dist) if mean_stop_dist > 0 else 0.0
    else:
        mae_capture_pct = 0.0
    avg_rr = (avg_win / abs(avg_loss)) if avg_loss != 0 else 0.0

    return PortfolioStats(
        total_trades=n,
        winners=n_w,
        losers=n_l,
        win_rate=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
        avg_pnl=avg_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        max_drawdown=max_dd_points,
        max_dd_dollars=max_dd_dollars,
        max_consecutive_losses=max_streak,
        doomsday_budget=doomsday_budget,
        mae_mean=mae_stats["mean"],
        mae_p10=mae_stats["p10"],
        mae_p30=mae_stats["p30"],
        mae_p50=mae_stats["p50"],
        mae_p70=mae_stats["p70"],
        mfe_mean=mfe_stats["mean"],
        mfe_p10=mfe_stats["p10"],
        mfe_p30=mfe_stats["p30"],
        mfe_p50=mfe_stats["p50"],
        mfe_p70=mfe_stats["p70"],
        mfe_capture_pct=mfe_capture_pct,
        mae_capture_pct=mae_capture_pct,
        avg_rr=avg_rr,
        stopout_rate_mae_p10=stopout_p10,
        stopout_rate_mae_p30=stopout_p30,
        stopout_rate_mae_p50=stopout_p50,
        stopout_rate_mae_p70=stopout_p70,
        target_hit_rate_mfe_p10=hit_mfe_p10,
        target_hit_rate_mfe_p30=hit_mfe_p30,
        target_hit_rate_mfe_p50=hit_mfe_p50,
        target_hit_rate_mfe_p70=hit_mfe_p70,
        mae_mfe_sync_pass=mae_mfe_sync_pass,
        kelly_pct=kelly,
        combined_edge=combined_edge,
        start_date=str(df["date"].min()),
        end_date=str(df["date"].max()),
        runtime_seconds=runtime_seconds,
        equity_curve=equity.tolist(),
    )


def stats_to_dict(s: PortfolioStats) -> dict:
    d = asdict(s)
    d.pop("equity_curve", None)  # too big for the summary table
    return d
