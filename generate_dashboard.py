"""Generate the summary dashboard report from the sweep CSVs.

Reads results/sweep_<symbol>_summary.csv files and emits a markdown report
plus a CSV with the top configurations.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RESULTS = Path("results")
OUT = RESULTS / "dashboard.md"


def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x:.1%}"


def fmt_dollar(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    return f"${x:,.0f}"


def fmt_x(x: float) -> str:
    if pd.isna(x) or x == float("inf"):
        return "n/a" if pd.isna(x) else "∞"
    return f"{x:.2f}x"


def generate(symbol: str, df: pd.DataFrame) -> str:
    md = [f"## {symbol}\n"]
    md.append(f"Total parameter sets tested: **{len(df)}**\n")
    md.append("### Top 10 by Profit Factor\n")
    md.append("| Stop | Entry | Target | Trades | Win% | PF | EV | AvgRR | ConsLoss | RoR Full | RoR 14d |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    top = df.sort_values("profit_factor", ascending=False).head(10)
    for _, r in top.iterrows():
        md.append(
            f"| {r['stop_basis']} | {r['entry_type']} | {r['target_type']} | "
            f"{int(r['total_trades'])} | {fmt_pct(r['win_rate'])} | {fmt_x(r['profit_factor'])} | "
            f"{fmt_dollar(r['expectancy'])} | {r['avg_rr']:.2f} | "
            f"{int(r['max_consecutive_losses'])} | {fmt_pct(r['ror_full'])} | {fmt_pct(r['ror_14day'])} |"
        )
    md.append("\n### Top 10 by Expectancy (EV per trade)\n")
    md.append("| Stop | Entry | Target | Trades | Win% | PF | EV | ConsLoss | Doomsday | RoR Full |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    top_ev = df.sort_values("expectancy", ascending=False).head(10)
    for _, r in top_ev.iterrows():
        md.append(
            f"| {r['stop_basis']} | {r['entry_type']} | {r['target_type']} | "
            f"{int(r['total_trades'])} | {fmt_pct(r['win_rate'])} | {fmt_x(r['profit_factor'])} | "
            f"{fmt_dollar(r['expectancy'])} | {int(r['max_consecutive_losses'])} | "
            f"{fmt_dollar(r['doomsday_budget'])} | {fmt_pct(r['ror_full'])} |"
        )

    md.append("\n### MAE / MFE percentiles (top 5 by PF)\n")
    md.append("| Stop | Entry | Target | MAE mean | MAE p30 | MAE p50 | MAE p70 | MFE mean | MFE p30 | MFE p50 | MFE p70 | MFE cap | MAE cap |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in top.head(5).iterrows():
        md.append(
            f"| {r['stop_basis']} | {r['entry_type']} | {r['target_type']} | "
            f"{r['mae_mean']:.1f} | {r['mae_p30']:.1f} | {r['mae_p50']:.1f} | {r['mae_p70']:.1f} | "
            f"{r['mfe_mean']:.1f} | {r['mfe_p30']:.1f} | {r['mfe_p50']:.1f} | {r['mfe_p70']:.1f} | "
            f"{fmt_pct(r['mfe_capture_pct'])} | {fmt_pct(r['mae_capture_pct'])} |"
        )

    md.append("\n### Day-of-week breakdown for best config\n")
    best = df.sort_values("profit_factor", ascending=False).iloc[0]
    md.append(f"Best config: **{best['stop_basis']} / {best['entry_type']} / {best['target_type']}**\n")
    md.append("(Day-of-week breakdown requires per-trade data; see `results/trades_*.csv`)\n")

    md.append("\n### Notes\n")
    md.append("- **EV** = expected value per trade (in dollars for the configured multiplier)")
    md.append("- **PF** = profit factor (gross profit / gross loss)")
    md.append("- **ConsLoss** = longest consecutive losing streak")
    md.append("- **Doomsday** = max drawdown / max consecutive losses (safe Risk Per Trade per Wolf)")
    md.append("- **RoR Full** = blowup rate over a 10k-sim Monte Carlo, full trade sequence")
    md.append("- **RoR 14d** = blowup rate within the first 14 trades (Wolf's kill zone)")
    md.append("- **MAE cap** = avg MAE / avg stop distance (lower = cleaner entries)")
    md.append("- **MFE cap** = avg win / avg MFE in points (higher = better exits)")
    return "\n".join(md)


def main() -> None:
    sections = ["# IB By Rejection — Parameter Sweep Results\n"]
    sections.append("**Wolf's framework applied:** All 54 parameter combinations tested with 2,000 Monte Carlo simulations each.\n")
    for sym in ("nq", "es"):
        path = RESULTS / f"sweep_{sym}_summary.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        sections.append(generate(sym.upper(), df))
    OUT.write_text("\n".join(sections))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
