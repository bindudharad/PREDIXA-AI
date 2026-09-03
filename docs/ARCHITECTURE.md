# ARCHITECTURE.md

## System Architecture - Consolidated View

## High-Level Data Flow

`
Data Sources (Polygon, Yahoo, SEC, NewsAPI, FRED)
         |
         v
Data Ingestion Layer (Batch + Incremental)
         |
         v
Data Validation & Quality (Schema, Range, Continuity, Outliers)
         |
         v
Data Storage (TimescaleDB + Parquet Data Lake)
         |
         v
Feature Engineering (8 groups, 101 features, lag enforcement)
         |
         v
Label Generation (3-class + 2-class, configurable horizons)
         |
         v
Dataset Builder (Walk-forward splits, expanding window, embargo)
         |
         v
ML Training Pipeline (Baseline -> Classical -> Ensemble -> DL)
         |
         v
Model Registry (MLflow, versioned, lineage, promotion workflow)
         |
         v
Prediction Engine (Feature store, inference, calibration, confidence)
         |
         v
Risk Engine (Position, Portfolio, Liquidity, Model uncertainty limits)
         |
         v
Ranking Engine (Probability + Expected return, filters)
         |
         v
Prediction Agent (Technical + News + Risk -> Decision Engine)
         |
         v
API Layer (FastAPI REST + WebSocket) + Dashboard (React/TS)
         |
         v
Monitoring (Drift detection, Performance, Data quality, Retraining)
`

## Component Details

### 1. Data Sources
- **Polygon.io**: Primary (OHLCV, trades, quotes, actions)
- **Yahoo Finance**: Backup (OHLCV, fundamentals)
- **Alpha Vantage**: Backup (OHLCV, fundamentals, macro)
- **SEC EDGAR**: Fundamentals
- **NewsAPI/RSS**: News articles
- **FRED**: Macro data (VIX, yields, DXY, commodities)

### 2. Data Ingestion
- Batch: Historical 10+ years
- Incremental: Daily updates at 18:00 ET
- Multi-provider failover
- Exchange calendar awareness

### 3. Data Validation
- Schema validation (types, constraints)
- Range checks (price > 0, high >= low)
- Continuity (no missing trading days)
- Outlier detection (z-score, IQR, ML)
- Quality reports per run

### 4. Data Storage
- **Raw Data Lake**: Parquet, partitioned by symbol/date, immutable
- **TimescaleDB**: Validated data, hypertables, compression
- **Feast**: Feature store (online Redis, offline Parquet)
- **MLflow**: Model registry, artifacts, metrics

### 5. Feature Engineering (8 Groups)
1. **Price**: Returns, log returns, momentum, gaps, ranges, rolling stats
2. **Technical**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ROC, volume
3. **Volatility**: Rolling vol, ATR, regime, changes, GARCH forecast
4. **Market-Relative**: Beta, relative strength vs SPY/sector, correlation, alpha
5. **Regime**: HMM states, SPY trend, vol regime, VIX, yield curve, DXY
6. **Fundamental**: EPS, revenue, P/E, P/B, ROE, D/E, margins (60d lag)
7. **News**: Count, sentiment, recency, intensity, credibility (1d lag)
8. **Macro**: VIX, yields, yield curve, DXY, oil, gold (1d lag)

### 6. Label Generation
- Horizons: 1, 5, 10, 20, 60 trading days
- 3-class: UP (>2%), DOWN (<-2%), SIDEWAYS (+-1%)
- 2-class: PROFITABLE (>0%), NOT_PROFITABLE (<=0%)
- Entry: Close of prediction day, Exit: Close of prediction day + horizon

### 7. Dataset Builder
- Expanding window (primary), Rolling window (alternative)
- Purged/embargoed splits (30-day gap)
- Versioned with content hashes
- Parquet export for training

### 8. ML Training Pipeline
- **Baseline**: Logistic Regression, Random Forest, Random
- **Classical**: XGBoost (primary), LightGBM, CatBoost
- **Deep Learning**: LSTM, GRU, TCN, Transformer (if justified)
- **HPO**: Optuna with temporal CV
- **Calibration**: Isotonic on held-out cal set

### 9. Model Registry
- Semantic versioning: model_{algo}_v{major}.{minor}.{patch}
- Metadata: dataset, features, labels, hyperparams, metrics
- Status: candidate -> shadow -> production -> archived
- Rollback capability

### 10. Prediction Engine
- Feature computation at prediction time (same as training)
- Load production model from registry
- Calibrated probabilities for all classes
- Confidence score (entropy-based)
- Ranking by P(UP) and expected return

### 11. Risk Engine
- Position: VaR, expected shortfall, max loss
- Portfolio: Correlation, factor exposure, concentration
- Liquidity: Days to liquidate, market impact
- Model uncertainty: Entropy, prediction intervals
- Hard limits (veto power)

### 12. Ranking Engine
- Primary: P(UP) descending
- Secondary: Expected return (probability-weighted)
- Filters: Min confidence, liquidity, market cap, sector diversification

### 13. Prediction Agent
- **Technical Agent**: XGBoost + SHAP
- **News Agent**: FinBERT sentiment + rules
- **Risk Agent**: Hard constraints (veto)
- **Decision Engine**: Weighted combination, conflict resolution, no-trade
- **Explainability**: SHAP + model contributions + natural language

### 14. API Layer
- FastAPI REST: predictions, performance, models, health
- WebSocket/SSE: Real-time prediction feed
- Auth: API keys, JWT
- Rate limiting, input validation

### 15. Dashboard
- Prediction explorer (historical + live)
- Performance analytics (metrics, calibration, attribution)
- Model comparison (production vs candidates)
- Drift monitoring (feature, prediction, performance)
- Backtest viewer (trade analysis, equity curves)

### 16. Monitoring
- **Drift**: PSI, KS test, ADWIN on features/predictions/performance
- **Performance**: Rolling metrics, regime-conditional
- **Data Quality**: Completeness, latency, anomalies
- **Retraining**: Scheduled + trigger-based orchestration
- **Experiment Tracking**: MLflow integration

## Key Design Principles

1. **Temporal Integrity**: No future data at any stage
2. **Explicit Versioning**: Data, features, models, datasets all versioned
3. **Separation of Concerns**: Prediction ≠ Trading; Research ≠ Production
4. **Observability First**: Metrics, logs, traces at every stage
5. **Fail-Safe Defaults**: Conservative limits, no-trade on uncertainty
6. **Human-in-the-Loop**: Model promotion requires approval
7. **Cost Awareness**: Transaction costs modeled from day one
