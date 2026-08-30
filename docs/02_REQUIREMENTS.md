# 02_REQUIREMENTS.md

## Functional Requirements

### FR-01: Market Data Collection
- **FR-01.1**: Collect historical OHLCV data for configurable universe of stocks (default: S&P 500 + liquid mid-caps)
- **FR-01.2**: Support multiple data providers (Yahoo Finance, Alpha Vantage, Polygon, IEX Cloud) with failover
- **FR-01.3**: Collect corporate actions (splits, dividends, mergers, spinoffs) for accurate price adjustment
- **FR-01.4**: Collect market indices (SPY, QQQ, DIA, IWM) and sector ETFs (XLF, XLK, XLE, etc.)
- **FR-01.5**: Support configurable data frequency (daily primary, hourly/15min optional)
- **FR-01.6**: Handle exchange calendars, holidays, and early closes correctly

### FR-02: Historical Data Ingestion
- **FR-02.1**: Batch ingestion of multi-year historical data with progress tracking
- **FR-02.2**: Incremental daily updates for live data refresh
- **FR-02.3**: Validate data completeness (no missing trading days, no gaps)
- **FR-02.4**: Detect and flag anomalous prices (extreme moves, zero volume, stale prices)
- **FR-02.5**: Store raw and adjusted prices separately for auditability

### FR-03: Data Validation
- **FR-03.1**: Schema validation (required columns, data types, constraints)
- **FR-03.2**: Range validation (prices > 0, volume >= 0, high >= low, high >= open/close)
- **FR-03.3**: Continuity validation (no duplicate dates, no missing trading days per symbol)
- **FR-03.4**: Cross-validation (adjusted close consistency with splits/dividends)
- **FR-03.5**: Outlier detection (z-score, IQR, ML-based anomaly detection)
- **FR-03.6**: Generate data quality report per ingestion run

### FR-04: Data Cleaning
- **FR-04.1**: Forward-fill missing values for non-trading days (holidays)
- **FR-04.2**: Handle stock splits using split-adjusted prices
- **FR-04.3**: Handle dividends using total return adjustment
- **FR-04.4**: Remove or flag delisted stocks with survivorship tracking
- **FR-04.5**: Standardize timestamps to UTC with exchange timezone awareness
- **FR-04.6**: Deduplicate records (same symbol, same timestamp)

### FR-05: Feature Generation
- **FR-05.1**: Price features (returns, log returns, momentum, gaps, ranges, rolling stats)
- **FR-05.2**: Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ROC, volume indicators)
- **FR-05.3**: Volatility features (rolling vol, ATR, regime, vol changes, GARCH forecasts)
- **FR-05.4**: Market-relative features (vs index, vs sector, relative strength, beta)
- **FR-05.5**: Market regime features (bull/bear/sideways, high/low vol, HMM states)
- **FR-05.6**: Fundamental features (EPS, revenue growth, P/E, P/B, ROE, D/E, margins)
- **FR-05.7**: News/sentiment features (count, sentiment score, recency, intensity, source credibility)
- **FR-05.8**: Macro features (VIX, yield curve, DXY, commodity prices, economic indicators)
- **FR-05.9**: All features computed using only data available at prediction time (no look-ahead)

### FR-06: Label Generation
- **FR-06.1**: Configurable prediction horizons (1D, 5D, 10D, 20D, 60D trading days)
- **FR-06.2**: Configurable return thresholds for classification (e.g., ±2% for UP/DOWN)
- **FR-06.3**: Support 3-class (UP/DOWN/SIDEWAYS) and 2-class (PROFITABLE/NOT_PROFITABLE) labels
- **FR-06.4**: Labels computed using forward-looking returns from entry to exit
- **FR-06.5**: Entry time = close of prediction date; Exit time = close of prediction date + horizon
- **FR-06.6**: Label leakage prevention: labels never used in feature computation

### FR-07: Dataset Builder
- **FR-07.1**: Build train/validation/test splits respecting temporal ordering
- **FR-07.2**: Support expanding window, rolling window, and purged cross-validation
- **FR-07.3**: Feature selection and correlation filtering
- **FR-07.4**: Class balancing (SMOTE, class weights, undersampling) with leakage prevention
- **FR-07.5**: Dataset versioning with hash-based reproducibility
- **FR-07.6**: Export datasets in parquet/feather for training pipeline

### FR-08: Model Training
- **FR-08.1**: Train baseline models (Logistic Regression, Random Forest)
- **FR-08.2**: Train classical ML models (XGBoost, LightGBM, CatBoost)
- **FR-08.3**: Train deep learning models (LSTM, GRU, Temporal CNN, Transformer) - optional
- **FR-08.4**: Hyperparameter optimization (Optuna, Bayesian optimization)
- **FR-08.5**: Cross-validation with temporal splits only
- **FR-08.6**: Early stopping with validation monitoring
- **FR-08.7**: Model checkpointing and artifact storage

### FR-09: Model Evaluation
- **FR-09.1**: Classification metrics (accuracy, precision, recall, F1, ROC-AUC, PR-AUC)
- **FR-09.2**: Probabilistic metrics (log loss, Brier score, calibration curves, reliability diagrams)
- **FR-09.3**: Per-class and macro/micro averaged metrics
- **FR-09.4**: Temporal stability metrics (performance across time periods)
- **FR-09.5**: Regime-conditional metrics (performance in bull/bear/sideways markets)
- **FR-09.6**: Statistical significance testing (bootstrap confidence intervals)

### FR-10: Prediction Generation
- **FR-10.1**: Generate predictions for all stocks in universe at prediction time
- **FR-10.2**: Output class probabilities for all classes (UP/DOWN/SIDEWAYS)
- **FR-10.3**: Output confidence score and prediction metadata
- **FR-10.4**: Batch prediction for backtesting; single prediction for live
- **FR-10.5**: Prediction timestamp = feature computation timestamp (no future data)

### FR-11: Probability Estimation
- **FR-11.1**: Calibrate raw model outputs to probabilities (Platt scaling, isotonic regression)
- **FR-11.2**: Validate calibration on held-out validation set
- **FR-11.3**: Report calibration metrics (ECE, MCE, Brier score decomposition)
- **FR-11.4**: Support temperature scaling for neural networks

### FR-12: Stock Ranking
- **FR-12.1**: Rank stocks by predicted probability of UP class
- **FR-12.2**: Rank by expected return (probability-weighted)
- **FR-12.3**: Filter by minimum confidence, liquidity, market cap
- **FR-12.4**: Sector/industry diversification constraints in ranking

### FR-13: Backtesting
- **FR-13.1**: Event-driven backtest engine (not vectorized)
- **FR-13.2**: Configurable entry/exit rules (next open, next close, VWAP, limit orders)
- **FR-13.3**: Position sizing (fixed, volatility-targeted, Kelly, risk parity)
- **FR-13.4**: Transaction costs: commission, spread, slippage, market impact
- **FR-13.5**: Portfolio constraints (max position, max sector, max drawdown, turnover)
- **FR-13.6**: Short selling support with borrow costs
- **FR-13.7**: Detailed trade log and portfolio time series output

### FR-14: Walk-Forward Validation
- **FR-14.1**: Expanding window (growing training set)
- **FR-14.2**: Rolling window (fixed training window size)
- **FR-14.3**: Configurable retraining frequency (monthly, quarterly, semi-annual)
- **FR-14.4**: Purged/embargoed validation to prevent leakage
- **FR-14.5**: Model selection on validation, final evaluation on test
- **FR-14.6**: Aggregate metrics across all folds with confidence intervals

### FR-15: Paper Trading
- **FR-15.1**: Simulate live predictions with real-time data feed
- **FR-15.2**: Execute paper trades at realistic prices (next open, VWAP, with slippage)
- **FR-15.3**: Track paper portfolio P&L, positions, cash, margin
- **FR-15.4**: Log every prediction before outcome known (audit trail)
- **FR-15.5**: Compare paper performance vs. backtest expectations
- **FR-15.6**: Alert on significant divergence (model drift)

### FR-16: Prediction Logging
- **FR-16.1**: Log every prediction with: timestamp, symbol, model version, features hash, prediction, probabilities, confidence, expected return
- **FR-16.2**: Log actual outcome when available: future price, realized return, correctness
- **FR-16.3**: Immutable append-only log (write-once)
- **FR-16.4**: Query predictions by date range, symbol, model version, outcome

### FR-17: Performance Tracking
- **FR-17.1**: Track prediction accuracy, calibration, and trading metrics over time
- **FR-17.2**: Rolling window metrics (30D, 90D, 180D)
- **FR-17.3**: Regime-conditional performance
- **FR-17.4**: Model comparison dashboard (production vs. candidates)
- **FR-17.5**: Attribution analysis (which features/models drove performance)

### FR-18: News/Sentiment Integration
- **FR-18.1**: Collect news from multiple sources (RSS, APIs, web scraping)
- **FR-18.2**: Entity recognition to link news to tickers
- **FR-18.3**: Sentiment classification (positive/negative/neutral) per article
- **FR-18.4**: Aggregate sentiment per symbol per day (weighted by source credibility)
- **FR-18.5**: News features computed with strict temporal cutoff (no future news)

### FR-19: Risk Analysis
- **FR-19.1**: Position-level risk (VaR, expected shortfall, max loss)
- **FR-19.2**: Portfolio-level risk (correlation, factor exposure, concentration)
- **FR-19.3**: Tail risk analysis (stress testing, historical scenarios)
- **FR-19.4**: Liquidity risk (days to liquidate, market impact)
- **FR-19.5**: Model uncertainty quantification (prediction intervals, entropy)

### FR-20: Agent Decision Making
- **FR-20.1**: Technical agent: analyzes price/volume features, outputs signal + confidence
- **FR-20.2**: News agent: analyzes sentiment, outputs signal + confidence
- **FR-20.3**: Risk agent: analyzes position/portfolio risk, outputs constraints
- **FR-20.4**: Decision engine: combines agent outputs with rules (veto, weighting, thresholds)
- **FR-20.5**: No-trade conditions (high uncertainty, conflicting signals, risk limits)
- **FR-20.6**: Explainable decision trail (why this prediction, why this action)

### FR-21: Model Monitoring
- **FR-21.1**: Track prediction distribution drift (KS test, PSI, Wasserstein distance)
- **FR-21.2**: Track feature distribution drift
- **FR-21.3**: Track performance metrics drift (accuracy, calibration, log loss)
- **FR-21.4**: Track data quality metrics (completeness, latency, anomalies)
- **FR-21.5**: Alert on threshold breaches (email, Slack, webhook)

### FR-22: Drift Detection
- **FR-22.1**: Statistical drift tests (KS, chi-square, PSI, ADWIN)
- **FR-22.2**: Concept drift detection (performance vs. expected)
- **FR-22.3**: Regime change detection (HMM, volatility clustering)
- **FR-22.4**: Automated retraining trigger on drift confirmation
- **FR-22.5**: Human-in-the-loop approval for model promotion

### FR-23: Retraining
- **FR-23.1**: Scheduled retraining (monthly/quarterly)
- **FR-23.2**: Trigger-based retraining (drift detected, performance degraded)
- **FR-23.3**: Candidate model training on updated dataset
- **FR-23.4**: Validation against production model on recent holdout
- **FR-23.5**: A/B test or shadow deployment before promotion
- **FR-23.6**: Rollback capability to previous model version

### FR-24: Dashboard/API Requirements
- **FR-24.1**: REST API for predictions, performance, models, health
- **FR-24.2**: Web dashboard: prediction explorer, performance charts, model comparison
- **FR-24.3**: Real-time prediction feed (WebSocket or SSE)
- **FR-24.4**: Experiment tracking UI (MLflow-style)
- **FR-24.5**: Backtest results viewer with trade analysis
- **FR-24.6**: Drift monitoring dashboard with alerts

## Non-Functional Requirements

### NFR-01: Reliability
- **NFR-01.1**: 99.9% uptime for prediction API during market hours
- **NFR-01.2**: Graceful degradation: serve stale predictions if model unavailable
- **NFR-01.3**: Automatic failover for data providers
- **NFR-01.4**: Idempotent operations for retries

### NFR-02: Reproducibility
- **NFR-02.1**: Every experiment fully reproducible from config + data version
- **NFR-02.2**: Fixed random seeds for all stochastic components
- **NFR-02.3**: Docker container for training/inference environments
- **NFR-02.4**: Dataset hashes recorded with every model artifact

### NFR-03: Scalability
- **NFR-03.1**: Support 1000+ symbols in prediction universe
- **NFR-03.2**: Feature computation < 5 seconds for full universe
- **NFR-03.3**: Batch prediction < 30 seconds for 1000 symbols
- **NFR-03.4**: Horizontal scaling for feature computation and prediction

### NFR-04: Security
- **NFR-04.1**: No hardcoded secrets; all credentials via environment variables/vault
- **NFR-04.2**: API authentication (API keys, JWT)
- **NFR-04.3**: Rate limiting on public endpoints
- **NFR-04.4**: Input validation and sanitization on all endpoints
- **NFR-04.5**: Audit logging for all prediction and model actions

### NFR-05: Observability
- **NFR-05.1**: Structured logging (JSON) with correlation IDs
- **NFR-05.2**: Metrics export (Prometheus): latency, throughput, errors, drift
- **NFR-05.3**: Distributed tracing for prediction pipeline
- **NFR-05.4**: Health checks for all services

### NFR-06: Performance
- **NFR-06.1**: Single prediction latency < 100ms (p99)
- **NFR-06.2**: Batch prediction (1000 symbols) < 30s
- **NFR-06.3**: Feature computation for 1000 symbols < 10s
- **NFR-06.4**: Model inference < 50ms per symbol

### NFR-07: Maintainability
- **NFR-07.1**: Modular architecture with clear interfaces
- **NFR-07.2**: Comprehensive unit/integration test coverage (>80%)
- **NFR-07.3**: Type hints and documentation for all public APIs
- **NFR-07.4**: CI/CD pipeline with automated testing

### NFR-08: Data Integrity
- **NFR-08.1**: ACID transactions for prediction logging
- **NFR-08.2**: Immutable raw data storage (append-only)
- **NFR-08.3**: Checksums for all data files and model artifacts
- **NFR-08.4**: Backup and disaster recovery for databases

---
