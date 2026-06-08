# Doomsday Budgeting — Wolf's Framework

*Source: The Daily Profiler / PackTrade Group. HTML at `wolf/doomsday_budget/doomsday_budget.html`.*

---

## The 6 Rules

### Rule 1 — The Data Foundation
**Only four data points: MAE + MFE + Time + Date.** Anything more is curve fitting.

- Collect clean data across bear, bull, and neutral market regimes
- No indicators, no confluences, no subjective notes
- The simpler your data, the more bulletproof your system

### Rule 2 — Test in Bear, Bull, and Neutral
- If your system fails in a specific regime, turn it off during that regime
- VIX spike (e.g., >120) is not a failure — it's data
- Most recent data matters most, but need history covering all three environments

### Rule 3 — Monte Carlo Your Worst Case
Take MAE/MFE data → run Monte Carlo → find absolute worst case → budget for it.

**Example:**
- Monte Carlo result: **15 consecutive losses**
- Account size: $2,000
- Risk Per Trade = $2,000 / 15 = **$133 per trade**

### Rule 4 — Account Rotation
When a single account can't cover the full drawdown needed, rotate across multiple accounts to **spread the damage**.

**Example:**
- 1 account limit: $2,000
- Required drawdown (from data): $3,500
- Solution: 2 accounts × $2,000 = $4,000 total

Rotate on every loss. When one account's health drops, move to the next fresh account.

### Rule 5 — Scale with Discipline
**Add accounts at 2x doomsday budget per account. Reduce when you drop below the threshold. No exceptions.**

| Threshold | Action |
|---|---|
| $1,000 bank | 1 account |
| Bank hits $2,000+ | +1 account |
| Bank drops below $2,000 | Reduce to 1 account |

### Rule 6 — Portfolio Diversification
Don't run all capital through a single strategy type. Combine systems that thrive in different conditions:

- **Momentum**: breakout/trend-following. Best when VIX elevated, market trending
- **Range/Continuation**: mean reversion. Best when VIX low, market in range
- **Algorithmic**: systematic rule-based execution

---

## Data Collection Framework

| Data Point | Description | Use |
|---|---|---|
| **MAE** | Max Adverse Excursion | Stop placement |
| **MFE** | Max Favorable Excursion | Target placement |
| **Time** | Session timestamp | When trade occurred |
| **Date** | Trading date | Day-of-week analysis |

### Data Collection Rule of Thumb
- Last quarter of data (recency)
- 1 quarter out of sample (validation)
- 1 quarter during volatile times (VIX spike)
- Samples across all three market types (bear, bull, neutral)

---

## Doomsday Budget Calculation

```
Doomsday Budget = Max Drawdown (from Monte Carlo)
Risk Per Trade  = Doomsday Budget / Max Consecutive Losses
```

**Example from slide:**
- Starting account: $2,000
- Max consecutive losses (Monte Carlo): 15
- Risk Per Trade = $2,000 / 15 = **$133**

---

## Key Insight
Budget for the **worst case**, not the average case. Survive the worst — everything else is gravy.
