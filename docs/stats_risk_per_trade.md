# Risk Per Trade — Wolf's Framework

*Source: Wolf Trading. HTML at `wolf/risk_per_trade/index.html`.*

---

## The 8 Golden Rules

### Rule 1 — Trade With the Trend
When you follow the trend, the market becomes your friend. Trend is defined by:
- **Uptrend**: Higher Highs and Higher Lows
- **Downtrend**: Lower Highs and Lower Lows

### Rule 2 — Know Your Risk/Reward Before Entry
Always know your R:R ratio **before** you enter. Reward must be at least **2:1** greater than risk. A negative R:R will destroy your account over time.

### Rule 3 — Never Risk More Than 2% Per Trade
The 2% rule protects your account from blowing up.

| Risk Per Trade | 10-Loss Drawdown | $100K Account |
|---|---|---|
| 2% | ~18.3% | $81,700 |
| 5% | ~40.1% | $60,000 |

### Rule 4 — Always Use a Stop Loss
Always place a stop loss before entering. A stop loss defines your risk — without it, you cannot properly size your position. Use technical analysis to set appropriate stop levels.

### Rule 5 — No News Trading
Do not trade during major news events. Spreads widen, slippage increases, and erratic price movements often work against you.

### Rule 6 — Cut Losses Quickly, Let Winners Run
Cut losses when price action invalidates your trade. Let winners run until momentum reverses. Don't lock in small gains only to miss larger moves.

### Rule 7 — Use Proper Position Sizing
Position sizing determines how much you risk per trade.
```
Position Size = (Account × Risk%) / Stop Loss Distance
```

### Rule 8 — Keep Trading Simple
Simple strategies are more robust and easier to execute. Complexity leads to overtrading and emotional decisions. Stick to your plan.

---

## Risk / Reward — Required Win Rate

| R:R Ratio | Account Multiplier | Required Win Rate |
|---|---|---|
| 1:1 | 2.0x | ~50% |
| 2:1 | 3.0x | ~33% |
| 3:1 | 4.0x | ~25% |
| 4:1 | 5.0x | ~20% |
| 5:1 | 6.0x | ~17% |
| 6:1 | 7.0x | ~14% |

---

## The 6 Key Metrics

| Metric | Full Name | Description |
|---|---|---|
| **EV** | Expected Value | Average dollar return per trade |
| **PF** | Profit Factor | Gross profit / gross loss |
| **MAE** | Max Adverse Excursion | Worst a trade moves against you |
| **MFE** | Max Favorable Excursion | Best a trade moves for you |
| **Con. Loss** | Consecutive Losses | Longest losing streak |
| **Max DD** | Max Drawdown | Deepest equity valley |

---

## Three Risk Strategies — $100,000 Account

| Strategy | Risk % | Per Trade | ~Daily Target | ~Monthly Target |
|---|---|---|---|---|
| Conservative | 1% | $1,000 | ~$500 | ~$10,000 |
| Moderate | 2% | $2,000 | ~$1,000 | ~$20,000 |
| Aggressive | 5% | $5,000 | ~$2,500 | ~$50,000 |

---

## Survival Math

```
Max Drawdown = Risk Per Trade × Max Consecutive Losses
```

**Example from slides:**
- Account: $4,500
- Risk Per Trade: $225 (5%)
- Max Consecutive Losses: 7
- Max Drawdown: 7 × $225 = $1,575
- Account survives 7 straight losses

---

## Position Sizing — Futures Example

```
Contracts = (Account × Risk%) / (Stop Distance in Points × $ Per Point)
```

**MNQ (Nasdaq-100 Micro):**
- $5 per point per contract
- Tighter stop (e.g., 10 pts) → more contracts for same dollar risk
- Wider stop (e.g., 30 pts) → fewer contracts

| Stop Type | Contracts | $ Per Point | Total Risk |
|---|---|---|---|
| Tight SL (10 pts) | 10 contracts | $100 | $1,000 |
| Wide SL (30 pts) | 3 contracts | $100 | $1,000 |

Same dollar risk, different contract count.

---

## The 4 Rules of Risk Per Trade

1. **Derived from Model Data** — EV, PF, MAE, MFE, consecutive losses, max drawdown define it. Never guess.
2. **The Denominator** — Every metric is measured against Risk Per Trade. Without it, nothing is actionable.
3. **Survive Worst Case** — Sized to survive max consecutive losses and deepest drawdown.
4. **Dynamic & Sustainable** — When model metrics change, Risk Per Trade adjusts. Built for survivability.

---

## When to Adjust Risk Per Trade

| Model Metrics Declining | Model Metrics Strong |
|---|---|
| Max drawdown exceeds tolerance | High Profit Factor |
| Consecutive losses increasing | Positive Expected Value |
| Profit factor dropping |
| **→ LOWER Risk Per Trade** | **→ RAISE Risk Per Trade slightly** |

---

## Fixed vs. Risk Per Trade Sizing

| | Fixed Sizing | Risk Per Trade |
|---|---|---|
| Stops | Open (varying distance) | Fixed dollar risk |
| Dollar risk per trade | Varies | Same every trade |
| Survivability | Undefined | Calculable |
| Model dependency | None | Requires EV, MAE, Max DD |

**Correct approach**: Set dollar risk first. Stop distance tells you how many contracts you can afford. Wider stop = fewer contracts. Tighter stop = more contracts. **Same dollar loss.**

---

## Partial Profit Taking — Pay for the Trade

Take partial profits at key levels to cover risk entirely:
- **1/4 off** (first target): ~50% of risk covered
- **1/2 off** (second target): ~75% of risk covered
- **3/4 off** (third target): Risk fully covered → free runner

Example (8 contracts total):
- Exit 2 contracts at first target
- Exit 3 contracts at second target
- Exit remaining at third target → runner is risk-free
