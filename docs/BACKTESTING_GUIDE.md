# BACKTESTING_GUIDE.md

## Backtesting Methodology Guide

This document describes the backtesting methodology for PREDIXA AI.

## Principles

1. **Event-driven, not vectorized**: Simulates actual order flow
2. **Realistic costs**: Commission, spread, slippage, market impact
3. **No look-ahead**: Only data available at decision time
4. **Walk-forward**: Same temporal splits as ML validation
5. **Separate prediction from trading**: Report both metrics

## Engine Architecture

`
For each prediction date:
  1. Get predictions for date
  2. Apply ranking and filters
  3. Calculate target positions (risk engine)
  4. Generate orders to reach targets
  5. Execute at next available price + costs
  6. Mark-to-market portfolio
  7. Record all state
`

## Entry/Exit Rules

| Rule | Description | Price Used |
|------|-------------|------------|
| next_open | Enter at next day open | Open(T+1) |
| next_vwap | Enter at next day VWAP | VWAP(T+1) |
| close_to_close | Enter at prediction close | Close(T) |

**Default**: next_open (most realistic for daily predictions made at close)

**Exit**: Fixed horizon (Close of T+horizon) - matches prediction definition

## Transaction Cost Model

`python
commission = max(1.0, min(0.005 * shares, 0.005 * trade_value))
spread_cost = 0.0010 * trade_value  # 10 bps
slippage = 0.0005 * sqrt(shares / avg_daily_volume) * trade_value  # square-root
total_cost = commission + spread_cost + slippage
`

## Position Sizing

- **Fixed fractional**: 5% max per position, scaled by signal strength
- **Volatility-targeted**: Scale to target portfolio volatility
- **Kelly**: Fraction = win_rate - (1-win_rate)/win_loss_ratio (capped)

## Portfolio Constraints

- Max position: 10% of portfolio
- Max sector: 30%
- Max gross exposure: 100% (long-only)
- Max turnover: 200% annually
- Min cash: 5%

## Metrics Reported

### Trading Metrics
- Total return (gross & net)
- CAGR (gross & net)
- Sharpe ratio (net, primary)
- Sortino ratio
- Calmar ratio
- Max drawdown & duration
- Ulcer index

### Trade Metrics
- Number of trades
- Win rate
- Avg win / avg loss
- Profit factor
- Expectancy
- Avg holding period
- Turnover

### Cost Metrics
- Total commission
- Total spread cost
- Total slippage
- Cost drag (bps/year)

### Prediction Metrics (on traded subset)
- Accuracy, log loss, Brier, ECE
- ROC-AUC
- Calibration

## Walk-Forward Backtest

Same folds as ML validation:
- Fold 1: Train 2015-2018, Val 2019, Test 2020
- Fold 2: Train 2015-2019, Val 2020, Test 2021
- Fold 3: Train 2015-2020, Val 2021, Test 2022
- Fold 4: Train 2015-2021, Val 2022, Test 2023
- Fold 5: Train 2015-2022, Val 2023, Test 2024

## Output Artifacts

1. Trade log (every trade with all metadata)
2. Daily portfolio snapshots
3. Equity curve
4. Drawdown series
4. Summary metrics (JSON)
5. Attribution analysis

## Validation

- Compare gross vs net returns
- Verify no look-ahead in execution prices
- Check constraint enforcement
- Validate against known benchmarks
