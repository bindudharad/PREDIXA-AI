# LIVE_PREDICTION_GUIDE.md

## Live/Paper Prediction Workflow

This document describes the live prediction and paper trading workflow.

## Daily Prediction Cycle

### Schedule
- **16:00 ET**: Market closes, prediction cycle begins
- **16:00-16:05**: Feature computation
- **16:05-16:10**: Model inference + calibration
- **16:10-16:15**: Risk filtering + ranking
- **16:15**: Predictions logged, paper trades generated
- **16:30**: Dashboard updated, alerts sent

### Feature Computation (Critical: No Look-Ahead)
- **Price/Technical/Volatility**: Use today's close (just printed)
- **Market-Relative**: Use yesterday's index close (safe)
- **Regime**: Use yesterday's macro data
- **Fundamentals**: 60-day lag from period end
- **News**: Up to 15:59 ET (1-min buffer before close)
- **Macro**: Previous day's close

### Prediction Output
Each prediction includes:
- Symbol, timestamp, model/feature versions
- Probabilities: P(UP), P(DOWN), P(SIDEWAYS)
- Confidence score (entropy-based)
- Expected return (probability-weighted)
- Predicted class, rank
- Explanation (SHAP + model contributions)

## Paper Trading Execution

### Order Generation
1. Rank predictions by P(UP) and expected return
2. Apply filters: min confidence, liquidity, sector limits
3. Calculate target positions (fixed fractional 5% max)
4. Generate orders to reach targets

### Execution Simulation
- **Entry**: Next trading day at open
- **Price**: Open + slippage (square-root model)
- **Costs**: Commission + spread + slippage
- **Exit**: At horizon (fixed) or stop loss

### Portfolio Management
- Mark-to-market daily at close
- Track cash, positions, P&L
- Enforce constraints (position, sector, exposure)
- Handle corporate actions (splits, dividends)

## Prediction Logging (Immutable, Pre-Outcome)

Every prediction logged BEFORE outcome known:
- All prediction metadata
- Feature hash for reproducibility
- Model version, feature version
- Rank, risk score, position size
- No-trade reason if applicable

## Outcome Resolution

Automated job runs daily:
- For predictions where horizon has passed
- Fetch entry/exit prices
- Calculate actual return and class
- Update prediction with outcome
- Calculate P&L if paper traded

## Monitoring & Alerts

### Real-Time
- Prediction count vs expected
- Feature computation latency
- Model inference latency
- API errors

### Daily (Post-Resolution)
- Rolling metrics (30/90/180 days)
- Calibration (ECE, reliability diagram)
- Prediction distribution drift (PSI)
- Feature drift (per-feature PSI)
- Performance vs backtest (divergence detection)

### Alert Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Prediction count | < 90% expected | < 50% |
| Log loss increase | > 10% | > 25% |
| ECE | > 0.05 | > 0.10 |
| Feature PSI (any) | > 0.1 | > 0.2 |
| Data freshness | > 2 hrs | > 6 hrs |

## Divergence Detection

`python
# Compare live metrics to backtest expectations
z_score = (live_metric - backtest_metric) / backtest_std
if abs(z_score) > 2.0:
    alert('Significant divergence detected')
`

## Manual Override

- **Pause predictions**: Emergency stop
- **Pause trading**: Stop paper trading, keep predicting
- **Model rollback**: Switch to previous production model (< 15 min)
- **Feature flag**: Disable specific feature groups

## Disaster Recovery

1. Data provider outage -> Failover to backup provider
2. Model service down -> Serve last predictions (stale < 1 hr)
3. Database down -> Read from cache, queue writes
4. Complete outage -> Alert on-call, manual prediction possible
