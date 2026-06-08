# IB By Rejection — Parameter Sweep Results

**Wolf's framework applied:** All 54 parameter combinations tested with 2,000 Monte Carlo simulations each.

## NQ

Total parameter sets tested: **54**

### Top 10 by Profit Factor

| Stop | Entry | Target | Trades | Win% | PF | EV | AvgRR | ConsLoss | RoR Full | RoR 14d |
|---|---|---|---|---|---|---|---|---|---|---|
| bottom | midpoint_only | ibh2_ibl2 | 3474 | 36.0% | 1.18x | $52 | 2.09 | 13 | 0.0% | 0.0% |
| ib25 | midpoint_only | ibh2_ibl2 | 3474 | 43.9% | 1.16x | $53 | 1.47 | 13 | 0.0% | 0.0% |
| points_50 | midpoint_only | ibh2_ibl2 | 3474 | 47.0% | 1.15x | $46 | 1.29 | 16 | 0.0% | 0.0% |
| ib25 | midpoint_only | ibh_ibl | 3474 | 59.7% | 1.15x | $38 | 0.77 | 7 | 0.0% | 0.0% |
| ib50 | midpoint_only | ibh2_ibl2 | 3474 | 48.0% | 1.14x | $53 | 1.23 | 9 | 0.0% | 0.0% |
| points_100 | midpoint_only | ibh2_ibl2 | 3474 | 51.6% | 1.14x | $49 | 1.05 | 8 | 0.0% | 0.0% |
| bottom | midpoint_only | ibh_ibl | 3474 | 51.4% | 1.13x | $30 | 1.07 | 9 | 0.0% | 0.0% |
| ib50 | midpoint_only | ibh_ibl | 3474 | 63.4% | 1.13x | $35 | 0.65 | 7 | 0.0% | 0.0% |
| points_100 | midpoint_only | ibh_ibl | 3474 | 66.9% | 1.12x | $32 | 0.55 | 6 | 0.0% | 0.0% |
| points_50 | midpoint_only | ibh_ibl | 3474 | 62.1% | 1.12x | $27 | 0.68 | 8 | 0.0% | 0.0% |

### Top 10 by Expectancy (EV per trade)

| Stop | Entry | Target | Trades | Win% | PF | EV | ConsLoss | Doomsday | RoR Full |
|---|---|---|---|---|---|---|---|---|---|
| ib25 | midpoint_only | ibh2_ibl2 | 3474 | 43.9% | 1.16x | $53 | 13 | $3,141 | 0.0% |
| ib50 | midpoint_only | ibh2_ibl2 | 3474 | 48.0% | 1.14x | $53 | 9 | $5,054 | 0.0% |
| bottom | midpoint_only | ibh2_ibl2 | 3474 | 36.0% | 1.18x | $52 | 13 | $3,174 | 0.0% |
| points_100 | midpoint_only | ibh2_ibl2 | 3474 | 51.6% | 1.14x | $49 | 8 | $5,265 | 0.0% |
| points_50 | midpoint_only | ibh2_ibl2 | 3474 | 47.0% | 1.15x | $46 | 16 | $2,028 | 0.0% |
| ib75 | midpoint_only | ibh2_ibl2 | 3474 | 50.3% | 1.11x | $42 | 8 | $6,058 | 0.0% |
| ib25 | either | ibh2_ibl2 | 4330 | 48.5% | 1.11x | $40 | 12 | $4,416 | 0.0% |
| points_150 | midpoint_only | ibh2_ibl2 | 3474 | 53.0% | 1.10x | $39 | 8 | $6,268 | 0.0% |
| ib50 | either | ibh2_ibl2 | 4330 | 51.4% | 1.10x | $39 | 8 | $5,831 | 0.0% |
| ib25 | midpoint_only | ibh_ibl | 3474 | 59.7% | 1.15x | $38 | 7 | $4,690 | 0.0% |

### MAE / MFE percentiles (top 5 by PF)

| Stop | Entry | Target | MAE mean | MAE p30 | MAE p50 | MAE p70 | MFE mean | MFE p30 | MFE p50 | MFE p70 | MFE cap | MAE cap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bottom | midpoint_only | ibh2_ibl2 | 22.2 | 6.4 | 11.1 | 24.0 | 34.8 | 6.6 | 14.7 | 31.8 | 141.9% | 81.0% |
| ib25 | midpoint_only | ibh2_ibl2 | 28.1 | 7.9 | 13.8 | 28.8 | 38.1 | 8.1 | 16.7 | 37.6 | 122.6% | 68.4% |
| points_50 | midpoint_only | ibh2_ibl2 | 25.8 | 9.3 | 18.6 | 40.3 | 35.2 | 9.3 | 17.0 | 33.8 | 111.9% | 51.5% |
| ib25 | midpoint_only | ibh_ibl | 23.9 | 5.9 | 11.0 | 23.0 | 22.6 | 6.1 | 11.0 | 24.9 | 112.9% | 58.1% |
| ib50 | midpoint_only | ibh2_ibl2 | 32.4 | 8.6 | 15.4 | 32.0 | 39.7 | 8.8 | 17.7 | 39.9 | 115.7% | 59.1% |

### Day-of-week breakdown for best config

Best config: **bottom / midpoint_only / ibh2_ibl2**

(Day-of-week breakdown requires per-trade data; see `results/trades_*.csv`)


### Notes

- **EV** = expected value per trade (in dollars for the configured multiplier)
- **PF** = profit factor (gross profit / gross loss)
- **ConsLoss** = longest consecutive losing streak
- **Doomsday** = max drawdown / max consecutive losses (safe Risk Per Trade per Wolf)
- **RoR Full** = blowup rate over a 10k-sim Monte Carlo, full trade sequence
- **RoR 14d** = blowup rate within the first 14 trades (Wolf's kill zone)
- **MAE cap** = avg MAE / avg stop distance (lower = cleaner entries)
- **MFE cap** = avg win / avg MFE in points (higher = better exits)
## ES

Total parameter sets tested: **54**

### Top 10 by Profit Factor

| Stop | Entry | Target | Trades | Win% | PF | EV | AvgRR | ConsLoss | RoR Full | RoR 14d |
|---|---|---|---|---|---|---|---|---|---|---|
| bottom | midpoint_only | ibh2_ibl2 | 2853 | 35.5% | 1.13x | $28 | 2.03 | 17 | 0.0% | 0.0% |
| bottom | either | ibh2_ibl2 | 3561 | 43.0% | 1.13x | $31 | 1.48 | 12 | 0.0% | 0.0% |
| ib25 | either | ibh2_ibl2 | 3561 | 48.6% | 1.13x | $33 | 1.18 | 11 | 0.0% | 0.0% |
| ib25 | midpoint_only | ibh2_ibl2 | 2853 | 43.8% | 1.12x | $30 | 1.42 | 15 | 0.0% | 0.0% |
| points_25 | either | ibh2_ibl2 | 3561 | 53.1% | 1.11x | $27 | 0.96 | 11 | 0.0% | 0.0% |
| ib25 | breakout_only | ibh2_ibl2 | 2800 | 55.4% | 1.10x | $24 | 0.87 | 7 | 0.0% | 0.0% |
| points_25 | breakout_only | ibh2_ibl2 | 2800 | 55.3% | 1.10x | $22 | 0.87 | 7 | 0.0% | 0.0% |
| bottom | breakout_only | ibh2_ibl2 | 2800 | 53.6% | 1.10x | $23 | 0.94 | 7 | 0.0% | 0.0% |
| points_50 | breakout_only | ibh2_ibl2 | 2800 | 57.1% | 1.09x | $20 | 0.80 | 7 | 0.0% | 0.0% |
| ib50 | either | ibh2_ibl2 | 3561 | 51.2% | 1.09x | $23 | 1.02 | 11 | 0.0% | 0.0% |

### Top 10 by Expectancy (EV per trade)

| Stop | Entry | Target | Trades | Win% | PF | EV | ConsLoss | Doomsday | RoR Full |
|---|---|---|---|---|---|---|---|---|---|
| ib25 | either | ibh2_ibl2 | 3561 | 48.6% | 1.13x | $33 | 11 | $2,055 | 0.0% |
| bottom | either | ibh2_ibl2 | 3561 | 43.0% | 1.13x | $31 | 12 | $1,720 | 0.0% |
| ib25 | midpoint_only | ibh2_ibl2 | 2853 | 43.8% | 1.12x | $30 | 15 | $1,422 | 0.0% |
| bottom | midpoint_only | ibh2_ibl2 | 2853 | 35.5% | 1.13x | $28 | 17 | $1,153 | 0.0% |
| points_25 | either | ibh2_ibl2 | 3561 | 53.1% | 1.11x | $27 | 11 | $2,204 | 0.0% |
| ib25 | breakout_only | ibh2_ibl2 | 2800 | 55.4% | 1.10x | $24 | 7 | $2,994 | 0.0% |
| ib50 | either | ibh2_ibl2 | 3561 | 51.2% | 1.09x | $23 | 11 | $2,413 | 0.0% |
| bottom | breakout_only | ibh2_ibl2 | 2800 | 53.6% | 1.10x | $23 | 7 | $3,099 | 0.0% |
| points_25 | breakout_only | ibh2_ibl2 | 2800 | 55.3% | 1.10x | $22 | 7 | $2,512 | 0.0% |
| ib75 | either | ibh2_ibl2 | 3561 | 52.7% | 1.08x | $21 | 11 | $3,045 | 0.0% |

### MAE / MFE percentiles (top 5 by PF)

| Stop | Entry | Target | MAE mean | MAE p30 | MAE p50 | MAE p70 | MFE mean | MFE p30 | MFE p50 | MFE p70 | MFE cap | MAE cap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bottom | midpoint_only | ibh2_ibl2 | 6.6 | 3.1 | 4.7 | 7.3 | 10.2 | 2.8 | 5.8 | 10.8 | 143.5% | 83.3% |
| bottom | either | ibh2_ibl2 | 8.4 | 3.4 | 5.5 | 8.9 | 10.4 | 3.4 | 6.6 | 11.3 | 132.5% | 67.8% |
| ib25 | either | ibh2_ibl2 | 9.8 | 4.0 | 6.5 | 10.5 | 11.1 | 3.9 | 7.3 | 12.1 | 122.0% | 59.9% |
| ib25 | midpoint_only | ibh2_ibl2 | 8.4 | 3.9 | 5.9 | 9.3 | 11.3 | 3.5 | 6.9 | 12.3 | 124.4% | 71.0% |
| points_25 | either | ibh2_ibl2 | 10.9 | 4.1 | 7.8 | 14.7 | 11.3 | 4.4 | 7.8 | 12.6 | 112.5% | 43.5% |

### Day-of-week breakdown for best config

Best config: **bottom / midpoint_only / ibh2_ibl2**

(Day-of-week breakdown requires per-trade data; see `results/trades_*.csv`)


### Notes

- **EV** = expected value per trade (in dollars for the configured multiplier)
- **PF** = profit factor (gross profit / gross loss)
- **ConsLoss** = longest consecutive losing streak
- **Doomsday** = max drawdown / max consecutive losses (safe Risk Per Trade per Wolf)
- **RoR Full** = blowup rate over a 10k-sim Monte Carlo, full trade sequence
- **RoR 14d** = blowup rate within the first 14 trades (Wolf's kill zone)
- **MAE cap** = avg MAE / avg stop distance (lower = cleaner entries)
- **MFE cap** = avg win / avg MFE in points (higher = better exits)