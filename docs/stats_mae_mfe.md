# MAE & MFE — Wolf's Framework

*Source: The Daily Profiler / PackTrade Group. HTML at `wolf/mfe_mae/mfe_mae.html`.*

---

## Definitions

### MAE — Maximum Adverse Excursion
The **worst unrealized loss** a trade experiences before it closes. It's the deepest a trade goes into the red while still open.

- Measures the **real cost of your entries**
- High MAE → bigger losses, deeper drawdowns, lower profit factor
- MAE percentiles define where your **stop** should go

### MFE — Maximum Favorable Excursion
The **peak unrealized profit** a trade reaches before you close it. The high-water mark.

- Measures the **true potential** the market offered
- Poorly captured MFE → smaller wins, weaker expectancy, leaving money on the table
- MFE percentiles define where your **targets** should go

---

## MFE Percentiles = Your Targets

Each MFE percentile tells you the **probability of the market reaching that level**.

| Percentile | Hit Rate | Use Case | Action |
|---|---|---|---|
| **MFE 10th** | 90% | Cover the Queen | Get risk-free (non-negotiable) |
| **MFE 25th–30th** | 70–75% | Cash Flow Target | Exit here on range days |
| **MFE 50th** | 50% | Extended Target | Need DMP/DWP or 3-hr line setup |
| **MFE 70th** | 30% | Runner Target | Only on strongly trending days |

### Capture Efficiency
```
MFE Capture % = Avg Win / Avg MFE
```
Example from slides: Avg MFE = $327.50, Avg Win = $250 → **76% captured**, 24% left on table.

---

## MAE Percentiles = Your Stops

The question: *If I place my stop at this percentile, how many times do I get stopped out?*

| Percentile | Stopout Rate | Use Case |
|---|---|---|
| **MAE 10th** | 90% | Entry zone (price returns here 90% of the time) |
| **MAE 30th** | 70% | Danger zone — can you sustain 70% stopouts? |
| **MAE 50th** | 50% | Coin flip zone |
| **MAE 70th** | 30% | Safe zone, but R:R worsens |

### Comparing MAE to Your Stop
```
If MAE Avg ($101) < Your Stop ($225):
→ MAE is less than half your stop
→ Your stops may be too wide
→ Tighten them based on data
```

---

## The 7 Rules

1. **Measure MAE and MFE** — The two master levers of your system
2. **MAE + MFE + Time + Date** — Anything more is curve fitting
3. **Compare MAE to Your Stop** — If MAE is small, your stops may be too wide
4. **Lower MAE** — Enter at cleaner levels, stop chasing, collect data manually
5. **MAE Percentiles Define Stops** — Data truth, not theory
6. **MAE/MFE Sync Is the Overfitting Filter** — Beautiful stats mean nothing without it
7. **Lower MAE + Capture More MFE = Stronger System** — Ripple effect on every metric

---

## The Opportunity Gap
```
Opportunity Gap = MFE (what the market offered) - Avg Win (what you took)
```

The gap between MFE and actual captures is the biggest source of inefficiency. Close that gap and every metric improves.

---

## MAE/MFE Sync Test (The Overfitting Filter)

Run this 3-part test on every strategy before trading live:

| Test | Result | Meaning |
|---|---|---|
| Historical Data | PASS | Backtested profitable |
| Monte Carlo Sim | PASS | Simulated profitable |
| **MAE/MFE Sync** | **FAIL** | Stops blown 80% of the time in live price |

> Without MAE/MFE sync, you're flying blind. Historical data and simulation both say profitable — but live price truth only comes from MAE and MFE.

---

## Ripple Effect
```
Smaller Avg Loss (lower MAE)
+
Bigger Avg Win (higher MFE capture)
=
Higher Profit Factor + Higher EV + Lower Drawdowns + Lower Risk of Ruin
```

---

## Quick Reference Card

| Metric | What It Measures | Target |
|---|---|---|
| MAE | Worst unrealized loss | Smaller = cleaner entries |
| MFE | Peak unrealized profit | Higher capture % = better exits |
| MFE 10 | 10th percentile high | 90% hit — get risk-free here |
| MFE 30 | 30th percentile high | 70% hit — cash flow target |
| MFE 50 | 50th percentile high | 50% hit — extended target |
| MFE 70 | 70th percentile high | 30% hit — runners only |
| MAE 30 | 30th percentile stop | 70% stopout — danger zone |
| MAE 50 | 50th percentile stop | 50% stopout — coin flip |
| MAE 70 | 70th percentile stop | 30% stopout — wide but safe |

---

## Golden Rule
> You can't say where your entry goes. You can't say where your stop goes. You can't say where your target goes — **until you have MAE and MFE.** That's why this is always step one.
