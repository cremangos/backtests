"""Monte Carlo Risk of Ruin simulator.

Per Wolf's framework:
- New accounts start at a random point on the equity curve (Rule 1, 14-day RoR)
- Run N simulations with shuffled trade sequences
- Track blowup rate -> full RoR
- Track blowup rate within first 14 trades -> 14-day RoR (kill zone)

Blowup definition: equity drops to <= 0 (or some threshold like 50% loss).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .engine import BacktestResult


@dataclass
class MonteCarloResult:
    ror_full: float            # blowup rate over full simulation
    ror_14day: float           # blowup rate in first 14 trades
    median_max_dd: float       # median max-drawdown across sims
    worst_max_dd: float        # 99th percentile max-drawdown
    median_final_equity: float # median ending equity
    n_simulations: int
    starting_equity: float
    risk_per_trade: float


def run_monte_carlo(
    result: BacktestResult,
    starting_equity: float = 10_000.0,
    risk_per_trade: float = 200.0,
    n_simulations: int = 10_000,
    kill_zone: int = 14,
    seed: int | None = 42,
) -> MonteCarloResult:
    """Run Monte Carlo sim by randomizing trade ordering.

    Each trade is converted to a fixed-$ gain/loss using the dollar pnl field,
    then re-sequenced randomly. We measure:
    - Full simulation RoR (equity <= 0 at any point)
    - 14-day RoR (equity <= 0 within first 14 trades)
    - Distribution of max-drawdown
    """
    if not result.trades:
        return MonteCarloResult(
            ror_full=0.0,
            ror_14day=0.0,
            median_max_dd=0.0,
            worst_max_dd=0.0,
            median_final_equity=starting_equity,
            n_simulations=0,
            starting_equity=starting_equity,
            risk_per_trade=risk_per_trade,
        )

    # Use the actual dollar pnl from the backtest (which already uses contract multiplier).
    pnls = np.array([t.pnl for t in result.trades], dtype=np.float64)
    # Scale so that the LARGEST LOSS in the sequence equals `risk_per_trade` dollars.
    # This treats risk_per_trade as "what the trader is willing to lose on the worst trade".
    max_loss = float(np.min(pnls))
    if max_loss < 0:
        scale = risk_per_trade / abs(max_loss)
    else:
        scale = 1.0
    scaled = pnls * scale

    rng = np.random.default_rng(seed)
    n_trades = len(scaled)
    full_blowups = 0
    kz_blowups = 0
    max_dds = np.empty(n_simulations, dtype=np.float64)
    final_equities = np.empty(n_simulations, dtype=np.float64)

    for i in range(n_simulations):
        # Random starting point on the equity curve (Rule 1)
        start_idx = int(rng.integers(0, n_trades))
        # Take a circular window of the same length as the trade sequence.
        idx = (np.arange(n_trades) + start_idx) % n_trades
        seq = scaled[idx]

        equity = starting_equity + np.cumsum(seq)
        full_blowup = bool((equity <= 0).any())
        kz_blowup = bool((equity[:kill_zone] <= 0).any()) if kill_zone <= n_trades else full_blowup
        full_blowups += int(full_blowup)
        kz_blowups += int(kz_blowup)

        running_max = np.maximum.accumulate(np.concatenate([[starting_equity], equity]))[1:]
        dd = running_max - equity
        max_dds[i] = dd.max()
        final_equities[i] = equity[-1]

    return MonteCarloResult(
        ror_full=full_blowups / n_simulations,
        ror_14day=kz_blowups / n_simulations,
        median_max_dd=float(np.median(max_dds)),
        worst_max_dd=float(np.percentile(max_dds, 99)),
        median_final_equity=float(np.median(final_equities)),
        n_simulations=n_simulations,
        starting_equity=starting_equity,
        risk_per_trade=risk_per_trade,
    )
