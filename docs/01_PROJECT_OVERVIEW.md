# 01_PROJECT_OVERVIEW.md

## Project Name
**PREDIXA AI** -- AI/ML Market Prediction Agent

## Vision
Build a rigorous, research-grade AI/ML system for stock market prediction that discovers whether machine learning models can identify a statistically meaningful and repeatable predictive edge on unseen and live market data -- without claiming certainty or guaranteeing profits.

## Problem Statement
Stock market prediction is one of the most challenging problems in applied machine learning due to:

1. **Non-stationarity**: Market dynamics change over time (regime shifts, structural breaks)
2. **Low signal-to-noise ratio**: Price movements contain very little predictable signal relative to noise
3. **Adaptive markets**: As strategies are discovered, they are arbitraged away (Efficient Market Hypothesis)
4. **Data leakage risks**: Subtle look-ahead bias can create false confidence in models
5. **Survivorship bias**: Historical datasets only contain surviving companies, inflating performance
6. **Overfitting**: High-dimensional feature spaces with limited samples invite overfitting
7. **Transaction costs**: Gross returns often disappear after realistic costs and slippage

## Motivation
- Determine if ML can provide a genuine edge beyond simple benchmarks
- Build a system that prioritizes scientific rigor over marketing claims
- Create a foundation for systematic, probability-based decision making
- Separate prediction performance from trading performance
- Enable continuous learning and model improvement through walk-forward validation

## Objectives

### Primary Objectives
1. **Probabilistic Prediction**: Estimate P(UP), P(DOWN), P(SIDEWAYS) for each stock over a defined horizon
2. **Statistical Rigor**: All evaluation on genuinely unseen, out-of-sample data via walk-forward validation
3. **Calibration**: Model probabilities must reflect true frequencies (reliability diagrams, Brier score)
4. **Cost-Aware**: Backtesting must include realistic transaction costs, slippage, and liquidity constraints
5. **Reproducibility**: Every experiment versioned, tracked, and reproducible

### Secondary Objectives
1. **Explainable Predictions**: Every prediction accompanied by factor attribution (SHAP, feature importance)
2. **Agent-Based Decisions**: Coordinate multiple specialized models (technical, sentiment, risk) into unified decision
3. **Live Monitoring**: Continuous drift detection, performance tracking, and automated retraining triggers
4. **Paper Trading**: Validate predictions in real-time before any capital allocation

## Scope

### In Scope
- Historical OHLCV data ingestion and validation
- Feature engineering (technical, fundamental, volatility, market-relative, regime)
- Label generation with configurable horizons and thresholds
- ML pipeline: baseline -> classical ML -> ensemble -> (optional) deep learning
- Walk-forward validation with expanding/rolling windows
- Backtesting with realistic costs
- Paper trading simulation with full prediction logging
- Model registry, versioning, and experiment tracking
- REST API for predictions and performance queries
- Dashboard for visualization and monitoring
- Drift detection and retraining workflow

### Out of Scope
- **Automatic real-money trading**: No live brokerage integration for actual order execution
- **High-frequency trading**: System operates at daily/weekly horizons, not microseconds
- **Crypto/forex/commodities**: Initial focus on equities only
- **Options/futures/derivatives**: Spot equity prediction only
- **Portfolio optimization**: Single-stock prediction focus; portfolio construction is separate
- **Regulatory compliance**: Research system, not production trading infrastructure
- **Real-time news trading**: News as feature input, not millisecond reaction system

## Target Users
- Quantitative researchers validating ML hypotheses
- Data scientists building market prediction models
- Portfolio managers seeking probability inputs (not signals)
- ML engineers studying time-series forecasting challenges
- Academic researchers needing reproducible market ML benchmark

## Expected System Behavior
1. **No Guarantees**: System outputs probabilities, not certainties
2. **Honest Evaluation**: Walk-forward results reported, not cherry-picked backtests
3. **Failure Visible**: Failed experiments logged and analyzed alongside successes
4. **Cost Realism**: All trading metrics net of estimated costs
5. **Audit Trail**: Every prediction timestamped, versioned, and traceable to model/features/data

## Key Assumptions
1. Daily frequency is sufficient for initial research (intraday adds complexity without clear edge)
2. US equity universe (S&P 500 + liquid mid-caps) provides adequate sample size
3. Public fundamental data (quarterly) has acceptable latency for research
4. News sentiment adds marginal value over price/volume alone (to be validated)
5. Market regimes can be identified and modeled as conditioning variables

## Limitations
1. **No Alpha Guarantee**: Most rigorous tests will likely show no statistically significant edge
2. **Data Quality**: Public data has errors, adjustments, and survivorship gaps
3. **Compute Constraints**: Deep learning experiments limited by GPU availability
4. **Lookback Window**: 5-10 years of clean data limits regime diversity
5. **Corporate Actions**: Splits, dividends, M&A require careful handling

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| No predictive edge found | High | Project concludes \ null result\ | Define success as rigorous methodology, not positive alpha |
| Data leakage in features | Medium | Invalid results | Strict temporal validation, leakage tests |
| Overfitting to noise | High | False confidence | Walk-forward, regularization, simple models first |
| Regime change breaks model | Medium | Live degradation | Drift detection, regime-conditioned models |
| Transaction costs eliminate edge | High | Backtest != live | Conservative cost modeling from day one |
| Survivorship bias inflates results | Medium | Invalid benchmarks | Use survivorship-bias-free datasets |

## Success Criteria
**Stage 1 (Research Foundation)**:
- Data pipeline ingests, validates, and stores 5+ years of clean OHLCV for 500+ stocks
- Feature engineering produces 100+ features with zero look-ahead bias
- Labels generated for 3-class (UP/DOWN/SIDEWAYS) and 2-class (PROFITABLE/NOT) problems
- Baseline models (logistic regression, random) trained and evaluated via walk-forward
- All experiments tracked, reproducible, versioned

**Stage 2 (Model Development)**:
- XGBoost/LightGBM outperform baseline on out-of-sample test periods
- Probability calibration achieved (Brier score < 0.25, reliability diagram near diagonal)
- Ensemble improves over best single model
- Feature importance stable across folds

**Stage 3 (Validation & Deployment)**:
- Walk-forward validation shows consistent edge across 3+ non-overlapping test periods
- Backtest with realistic costs (10bps + slippage) shows positive expectancy
- Paper trading runs 3+ months with prediction logging
- Drift detection alerts on performance degradation

**Stage 4 (Agent & Explainability)**:
- Agent coordinates technical + sentiment + risk models
- Every prediction has SHAP-based explanation
- API serves predictions with <500ms latency
- Dashboard shows live performance vs. benchmarks
