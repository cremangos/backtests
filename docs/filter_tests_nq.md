# NQ Filter Test Log

Running record of every filter hypothesis tested on the NQ 2-year backtest
(240 trades, 2024-06-03 → 2026-05-27, recommended config: be=75, trail=15,
stop=bottom, entry=midpoint_only, target=ibh_ibl, strict 10:30+).

Purpose: don't re-test things we've already tried. When a new filter is
proposed, add a row BEFORE running the test so we have a clean trail.

## Baseline (no filters)
- n=240, WR=55.8%, net=+$29,654, EV=+$124
- Combined edge ≈ 92.3

---

## IB range filters

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 1 | Skip IB < 50 pts | 225 | 56.4% | +$29,737 | 2026-06-09 | tiny improvement; kept as candidate |
| 2 | Skip IB < 75 pts | 181 | 58.0% | n/a | 2026-06-09 | moderate |
| 3 | Skip IB < 100 pts | 137 | 58.4% | n/a | 2026-06-09 | moderate |
| 4 | Skip IB > 200 (huge IB) | 212 | 55.7% | n/a | 2026-06-09 | no signal alone |
| 5 | **Skip SHORT if IB > 200** | 225 | n/a | n/a | 2026-06-09 | -$4,438 pattern removed (15 trades, 53.3% WR, net -$4,438) |

## IB close position (where did price close at 10:29?)

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 6 | Quintile breakdown | 240 | 50.6%–63.2% | mixed | 2026-06-09 | Q3 (mid) worst; extremes good |
| 7 | **Skip SHORT when close in upper half of IB (≥ 0.5)** | 195 | 57.4% | +$34,299 | 2026-06-09 | **Best single non-VWAP filter** |
| 8 | Skip LONG when close in lower half of IB | n/a | n/a | n/a | — | NOT TESTED — long-below-mid is +$13,440 (62.8% WR), not a loss pattern |
| 9 | Skip when close in middle quintile (Q3, 0.4–0.6) | n/a | n/a | n/a | — | NOT TESTED — Q3 was worst bucket |
| 9a | **Direction must match close half (LONG only if close > mid, SHORT only if close < mid)** | 152 | 55.9% | +$20,859 | 2026-06-09 | **NO win — drops net P&L by $8,795**; the long-below-mid bucket is +$13,440 (62.8% WR), so filtering it loses more than the short-above-mid bucket saves |
| 9b | Skip when close in middle 50% (0.25–0.75) | 69 | 55.1% | +$7,598 | 2026-06-09 | worse — throws away too much |
| 9c | Skip when close in middle 80% (extreme 20% only) | 47 | 57.4% | +$7,106 | 2026-06-09 | small sample, modest |
| 9d | Tighter + direction (long if top 25%, short if bottom 25%) | 56 | 53.6% | +$3,270 | 2026-06-09 | worse — overfit |

## IB formation timing (when in the 60-min window did IBL/IBH form?)

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 10 | Skip if IBL formed late (≥ 30 min in) | 145 | 57.9% | +$29,787 | 2026-06-09 | mild — IBL-late is -$133 group |
| 11 | Skip if IBH formed early (< 30 min in) | 114 | 59.6% | +$23,578 | 2026-06-09 | mild — IBH-late is +$23,578 group |

## Entry timing

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 12 | Skip first 5 min of RTH (09:30–09:35) | n/a | n/a | n/a | 2026-06-09 | BACKWARDS — engine is already STRICT (entries ≥ 10:30); the "09:30 entry" was a TZ display bug in my analysis, not real |
| 13 | Entry within X min of 10:30 sweep | 135–221 | 52.6%–56.6% | mixed | 2026-06-09 | first 5 min lowest WR, but filter adds little net |

## Day of week

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 14 | Skip Tuesday | 193 | 57.5% | n/a | 2026-06-09 | Tue is 42.6% WR (-$7,698); but other days vary too, hard to call without more data |

## VWAP alignment (session VWAP, RTH open → entry)

| # | Rule | n kept | WR | Net | Date tested | Verdict |
|---|---|---|---|---|---|---|
| 15 | **Long entry must be above VWAP** | 38 (longs) | **71.1%** | +$14,052 | 2026-06-09 | **Best signal in study** |
| 16 | **Short entry must be below VWAP** | 49 (shorts) | 59.2% | +$5,185 | 2026-06-09 | removes the -$3,274 short-above-VWAP bucket |
| 17 | Either direction (long-above or short-below) | 87 | **64.4%** | +$19,237 | 2026-06-09 | **best combined WR; cuts trade count to 87/240** |
| 18 | VWAP + skip-short-close-hi combined | 66 | 63.6% | +$13,807 | 2026-06-09 | rules overlap; close-hi redundant after VWAP |

## Combined edge (BE=75, trail=15, contract mult $20)

| # | Config | n | WR | EV | Combined edge | Date tested |
|---|---|---|---|---|---|---|
| 19 | Baseline | 240 | 55.8% | $124 | 92.3 | 2026-06-09 |
| 20 | + Skip short-close-hi | 195 | 57.4% | $176 | **133** | 2026-06-09 |
| 21 | + VWAP alignment | 87 | 64.4% | $221 | **178** | 2026-06-09 |

---

## Things that were proposed but turned out to be bugs

- "Top 5 losses entered at 09:30–09:32" — that was a timezone display bug in
  my analysis (Python's `astimezone()` fell back to system EST instead of ET).
  Real entry times are 10:30–10:32. So filter #12 is invalid.

## Things we've considered but not tested

- 1-min vs 5-min entry trigger (do we need a 1-bar close confirmation?)
- IB quality (was the IB range composed of a few fat wicks or many small bars?)
- Pre-market volume (globex volume into 09:30 — high vs low)
- News day filter (FOMC, CPI, NFP — already partly handled by month effect)
- Cross-asset confirmation (ES vs NQ, YM vs NQ at 10:30 — is one leading?)
- VIX regime (above 25 vs below)
- Spread/liquidity filter (skip first/last 5 min of RTH)
- Time-of-day VWAP slope (is VWAP rising or falling at entry?)

When testing a new filter, add it to the table above FIRST so we know we've
considered it.
