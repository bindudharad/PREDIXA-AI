# 26_RISK_AND_LIMITATIONS.md

## Risks and Limitations

This document clearly documents all known risks and limitations.

## Fundamental Limitations

### No Guaranteed Prediction
- Markets are complex adaptive systems
- Efficient Market Hypothesis: edges are arbitraged away
- Past performance does not guarantee future results
- System outputs probabilities, NOT certainties

### Market Regime Changes
- Bull/bear/sideways regimes have different dynamics
- Structural breaks (2008, 2020, 2022) invalidate models
- Model trained on one regime may fail in another
- Regime detection is itself uncertain

### Data Quality Issues
- Public data has errors, adjustments, gaps
- Survivorship bias in historical datasets
- Corporate action adjustments imperfect
- Fundamental data has reporting lag (60+ days)
- News sentiment noisy and incomplete

### Overfitting Risk
- High-dimensional feature space (100+ features)
- Limited samples (~500 stocks x 250 days x 5 years = 625K)
- Financial time series highly autocorrelated
- Easy to find spurious patterns
- Walk-forward validation essential but not foolproof

### Transaction Costs
- Gross returns often disappear after costs
- Slippage varies with liquidity, volatility
- Spread costs significant for small caps
- Borrow costs for shorts can be high
- Tax impact on short-term gains

### Slippage & Liquidity
- Model assumes fill at next open/VWAP
- Real fills may be worse
- Large positions move market
- Illiquid stocks: partial fills, high impact

### Unexpected Events
- Earnings surprises
- Geopolitical events
- Fed policy changes
- Black swans (COVID, flash crashes)
- No model can predict true surprises

### Model Drift
- Concept drift: relationship changes
- Data drift: feature distributions shift
- Regime drift: market structure changes
- Requires continuous monitoring and retraining

### False Confidence
- Well-calibrated model can still lose money
- High confidence on wrong predictions
- Confidence is epistemic, not aleatoric
- Over-reliance on model output

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data provider outage | Medium | High | Multi-provider failover |
| Model API failure | Low | High | Fallback to last predictions |
| Drift undetected | Medium | High | Automated monitoring + alerts |
| Bad model promoted | Low | Critical | Shadow deployment, human approval |
| Backtest overfit | High | High | Walk-forward, embargo, costs |
| Survivorship bias | Medium | Medium | Track delistings, use PIT data |
| Feature leakage | Low | Critical | Automated leakage tests in CI |

## System Constraints

### Initial Scope (v1)
- Daily frequency only (no intraday)
- US equities only (S&P 500 + liquid mid-caps)
- Spot prediction only (no options, futures, crypto)
- Long-only paper trading (no short selling)
- No portfolio optimization (single-stock focus)
- Research mode only (no real money)

### Computational
- CPU-only for classical ML (v1)
- GPU optional for deep learning (v2+)
- Training time < 5 min per walk-forward fold
- Inference < 100ms per 1000 symbols

### Data Latency
- EOD data: available ~18:00 ET
- Fundamentals: 60+ day lag
- News: near real-time but noisy
- Macro: 1-day lag

## Ethical Considerations

- No automated real-money trading
- Clear disclaimer: research tool only
- No financial advice
- Transparent about limitations
- Audit trail for all predictions

## Regulatory

- Not a registered investment advisor
- No fiduciary duty
- Paper trading only
- No client funds
- Compliance with data provider ToS

## Summary

**The system is a research tool for discovering whether ML can find a repeatable edge. It does not guarantee profits. All results must be validated out-of-sample with realistic costs before any capital allocation.**
