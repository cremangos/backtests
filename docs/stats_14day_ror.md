# 14-Day Risk of Ruin — Wolf's Framework

*Source: The Daily Profiler / PackTrade Group. HTML index at `wolf/14-day-risk-of-ruin/index.html`.*

---

## The 6 Rules

### Rule 1 — The Kill Zone
Every new account starts at a **random point on the equity curve**. You cannot choose where you start — you land randomly. Every strategy added to the account is another random entry point on another equity curve. If any strategy is in a losing period, it drags the whole account down.

- **First 14 days** are statistically the most dangerous
- At 60% win rate, there is a **65% chance** of hitting 5+ consecutive losses in the first 100 trades
- Every added strategy **multiplies kill zone risk**

### Rule 2 — Perpetual Day Zero
Prop firms keep you at perpetual day zero:
- Pass the eval → Day 0
- Get funded → Day 0
- Take a payout → reset closer to Day 0
- Blow the account → Day 0

**Every reset restarts the 14-day kill zone clock.**

### Rule 3 — The Ralph Vince Rule
In 1992, Ralph Vince ran an experiment with **40 PhDs**. He gave them a mathematically guaranteed winner: 60% win rate, 1:1 payout, 100 trials, starting with $1,000.

| Result | Value |
|--------|-------|
| Blew up | **95%** |
| Survived | **5%** (only 2 PhDs) |

**10 Consecutive Losses at Different Risk Levels:**

| Risk Per Trade | Drawdown | Outcome |
|---|---|---|
| 1% | 9.6% | Survivable |
| 2% | 18.3% | Painful but alive |
| 5% | 40.1% | Account in danger |
| 10% | 65.1% | Game over |
| 20% | 89.3% | Blown |

- Van Tharp's research: **position sizing accounts for 60% of trading success**
- **The edge is never the problem — the sizing is.**

### Rule 4 — Initial Balance Only
Size off your **starting balance**, never your rolling P&L.

- Rolling P&L resets you to Day 0 every time you adjust
- Size off the initial balance until buffer is **2x–3x**
- **1% risk per trade maximum in the kill zone**

### Rule 5 — One Strategy First
Each additional strategy on a new account is another random entry point. Trade **one strategy** until buffer is built.

**Buffer Milestones:**
```
$2K Start → Single strategy → Build buffer → $4K (2x) → Earn right to add 2nd → $6K (3x) → Safe to size up
```

### Rule 6 — Account Rotation
Set up **2–3 accounts**. Rotate on losses. Sideline the sick account. Think **quarter-over-quarter**, not day-over-day.

- Day-over-Day: emotional reactions, revenge trading, size up after wins
- 90-Day Thinking: quarter-over-quarter, survive and compound, rotate sick accounts

---

## Position Sizing Reference

| Risk Per Trade | 10-Loss Drawdown | Account Status at $10K |
|---|---|---|
| 1% | ~9.6% | Healthy |
| 2% | ~18.3% | Underwater but alive |
| 5% | ~40.1% | Danger zone |
| 10% | ~65.1% | Likely blown |

---

## Key Metrics to Track

| Metric | Target |
|--------|--------|
| Max Consecutive Losses | From trade history |
| Max Drawdown | From backtest |
| Risk Per Trade | MaxDD / MaxConsecutiveLosses |
| Kill Zone Horizon | 14 trading days |
| Buffer Threshold | 2x–3x initial balance |
