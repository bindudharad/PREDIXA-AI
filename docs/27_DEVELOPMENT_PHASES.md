# 27_DEVELOPMENT_PHASES.md

## Development Phases

This document creates a detailed implementation roadmap.

## Phase 0: Problem Definition (Week 1)

**Goal**: Define exact prediction problem, success criteria, scope

**Inputs**: Business requirements, market knowledge
**Outputs**: 
- Signed-off problem definition
- Success criteria document
- Scope boundaries

**Tasks**:
- Define prediction horizons (5, 20 days)
- Define classification thresholds (2% UP/DOWN, 1% SIDEWAYS)
- Define universe (S&P 500 + liquid mid-caps)
- Define success criteria (log loss, Sharpe, calibration)
- Document out-of-scope items

**Dependencies**: None
**Validation**: Stakeholder sign-off
**Completion**: Problem definition document approved

---

## Phase 1: Data Collection (Weeks 2-3)

**Goal**: Build robust data ingestion pipeline

**Inputs**: Data provider APIs (Polygon, Yahoo, Alpha Vantage)
**Outputs**: 
- Raw OHLCV data (10 years, 500+ symbols)
- Corporate actions
- Market indices
- Sector ETFs

**Tasks**:
- Implement multi-provider ingestion with failover
- Handle exchange calendars, holidays
- Store raw data in data lake (Parquet, partitioned)
- Implement incremental daily updates
- Data quality reports per ingestion run

**Dependencies**: Phase 0
**Validation**: 
- 5+ years clean data for 500+ symbols
- No missing trading days
- Corporate actions correctly captured
- Quality reports generated

**Completion**: Data lake populated, ingestion automated

---

## Phase 2: Data Cleaning (Week 4)

**Goal**: Clean, validate, adjust data

**Inputs**: Raw data from Phase 1
**Outputs**: Validated, adjusted price data in TimescaleDB

**Tasks**:
- Schema validation
- Range/continuity checks
- Outlier detection
- Split/dividend adjustment (total return)
- Survivorship tracking (delistings with dates)
- Timestamp standardization (UTC)
- Deduplication

**Dependencies**: Phase 1
**Validation**:
- Zero schema violations
- Adjusted prices match recomputed from actions
- Delistings tracked with reasons
- Quality report per symbol

**Completion**: Clean data in TimescaleDB, validation automated

---

## Phase 3: Feature Engineering (Weeks 5-6)

**Goal**: Compute all feature groups with zero leakage

**Inputs**: Clean OHLCV, indices, fundamentals, news, macro
**Outputs**: Feature store (Feast) with versioned features

**Tasks**:
- Price features (returns, momentum, gaps, ranges)
- Technical indicators (SMA, EMA, RSI, MACD, BB, ATR, volume)
- Volatility features (rolling vol, regime, GARCH)
- Market-relative (beta, relative strength vs SPY/sector)
- Regime features (HMM, trend, vol regime, VIX, yields)
- Fundamental features (EPS, revenue, P/E, ROE, margins - 60d lag)
- News features (sentiment, count, recency - 1d lag)
- Macro features (VIX, yields, DXY, commodities - 1d lag)
- Feature pipeline with temporal integrity enforcement
- Feature versioning (hash of code + config)

**Dependencies**: Phase 2
**Validation**:
- Automated leakage tests pass
- Feature store online = offline consistency
- Version hashes recorded
- 100+ features computed

**Completion**: Feature store operational, versioned

---

## Phase 4: Label Generation (Week 7)

**Goal**: Generate labels for all horizons and threshold configs

**Inputs**: Adjusted prices, prediction definition
**Outputs**: Versioned labels in feature store

**Tasks**:
- Forward return calculation (close-to-close)
- 3-class labels (UP/DOWN/SIDEWAYS)
- 2-class labels (PROFITABLE/NOT)
- Configurable horizons (1, 5, 10, 20, 60 days)
- Configurable thresholds (1%, 1.5%, 2%, 2.5%, 3%)
- Label versioning
- Class distribution analysis

**Dependencies**: Phase 2
**Validation**:
- No forward-looking leakage in label code
- Class distributions within expected ranges
- Label version hashes recorded
- Consistency checks pass

**Completion**: Labels generated and versioned

---

## Phase 5: EDA (Week 8)

**Goal**: Understand data, features, labels

**Inputs**: Features, labels from Phases 3-4
**Outputs**: EDA report, feature selection candidates

**Tasks**:
- Feature distributions, correlations
- Label distributions per horizon/threshold
- Feature-target correlations
- Regime-conditional analysis
- Missing value patterns
- Outlier analysis
- Feature stability across time

**Dependencies**: Phases 3-4
**Validation**: EDA report with actionable insights
**Completion**: EDA report delivered, feature selection plan

---

## Phase 6: Baseline ML (Weeks 9-10)

**Goal**: Establish baseline models

**Inputs**: Datasets from Phase 4 (walk-forward splits)
**Outputs**: Trained baseline models, walk-forward results

**Tasks**:
- Implement walk-forward validation (expanding, 5 folds, 30-day embargo)
- Train Logistic Regression (L2, balanced)
- Train Random Forest (baseline non-linear)
- Random prediction baseline
- Buy-and-hold benchmark
- Evaluate: log loss, Brier, ECE, ROC-AUC, accuracy
- Bootstrap confidence intervals
- Regime-conditional metrics
- Statistical significance vs random

**Dependencies**: Phases 3-4
**Validation**:
- Logistic Regression beats random on walk-forward test
- All metrics computed with CIs
- No leakage in validation

**Completion**: Baseline models trained, evaluated, documented

---

## Phase 7: Advanced ML (Weeks 11-12)

**Goal**: Train XGBoost, LightGBM, compare

**Inputs**: Same datasets, baseline results
**Outputs**: Classical ML models, comparison

**Tasks**:
- XGBoost with Optuna HPO (temporal CV)
- LightGBM with Optuna HPO
- CatBoost (optional)
- Hyperparameter optimization per fold
- Early stopping on validation
- Calibration (isotonic) on held-out calibration set
- Compare vs baselines (statistical tests)
- Feature importance stability across folds

**Dependencies**: Phase 6
**Validation**:
- XGBoost/LightGBM beat Logistic Regression significantly
- Calibration ECE < 0.05
- Feature importance stable (Spearman > 0.7)
- No overfitting (train/val gap small)

**Completion**: Classical ML models trained, best selected

---

## Phase 8: Ensemble (Week 13)

**Goal**: Combine models for better predictions

**Inputs**: Trained models from Phase 7
**Outputs**: Ensemble model, ensemble evaluation

**Tasks**:
- Weighted average ensemble (inverse validation log-loss weights)
- Stacking meta-learner (Logistic Regression on predictions)
- Voting ensemble
- Regime-conditioned weights (optional)
- Calibration on ensemble (post-hoc)
- Compare ensemble vs best single model
- Model contribution analysis

**Dependencies**: Phase 7
**Validation**:
- Ensemble beats best single model on test
- Calibration maintained/improved
- Weights stable across folds

**Completion**: Ensemble model ready

---

## Phase 9: Backtesting (Weeks 14-15)

**Goal**: Realistic backtesting with costs

**Inputs**: Ensemble predictions, price data
**Outputs**: Backtest results, trade analysis

**Tasks**:
- Event-driven backtest engine
- Entry: next open, Exit: fixed horizon
- Transaction costs (commission, spread, slippage)
- Position sizing (fixed fractional 5% max)
- Portfolio constraints (sector, gross, turnover)
- Trade logging with all metadata
- Performance metrics (Sharpe, Sortino, max DD, profit factor)
- Attribution: prediction vs sizing vs risk mgmt
- Walk-forward backtest (same folds as ML)

**Dependencies**: Phase 8
**Validation**:
- Net Sharpe > 1.0 after costs
- Max DD < 20%
- Profit factor > 1.2
- Cost drag < 50 bps/year
- Results stable across folds

**Completion**: Backtest framework operational, results documented

---

## Phase 10: Walk-Forward Validation (Week 16)

**Goal**: Full walk-forward validation of complete pipeline

**Inputs**: All previous phases
**Outputs**: Final walk-forward report

**Tasks**:
- Run complete pipeline on 5+ folds
- Aggregate metrics with bootstrap CIs
- Stability analysis (CV < 10%, no trend)
- Regime-conditional performance
- Model selection on validation, report on test
- Compare against benchmarks (random, buy-hold, momentum, MA)
- Document all failures and successes

**Dependencies**: Phases 1-9
**Validation**:
- Consistent edge across 3+ test periods
- Statistical significance vs benchmarks
- No leakage detected
- Reproducible results

**Completion**: Walk-forward validation report

---

## Phase 11: Paper Trading (Weeks 17-20)

**Goal**: Live paper trading validation

**Inputs**: Production model, live data feeds
**Outputs**: 3+ months paper trading track record

**Tasks**:
- Live prediction scheduler (16:00 ET daily)
- Feature computation at prediction time (same as training)
- Model inference with production model
- Risk engine filtering
- Paper trading engine (next open execution + costs)
- Prediction logging (immutable, pre-outcome)
- Outcome resolution (automated)
- Performance tracking (rolling metrics)
- Divergence detection (backtest vs live)
- Dashboard for monitoring

**Dependencies**: Phase 10
**Validation**:
- 3+ months continuous operation
- Prediction logging complete
- Live metrics within backtest confidence intervals
- No critical alerts
- Divergence alerts working

**Completion**: Paper trading validated, ready for monitoring

---

## Phase 12: News + Sentiment (Weeks 21-22)

**Goal**: Add news sentiment features

**Inputs**: News APIs, FinBERT
**Outputs**: News features integrated, re-evaluated models

**Tasks**:
- News ingestion (RSS, NewsAPI, webhooks)
- Entity recognition (ticker linking)
- Sentiment classification (FinBERT)
- Daily aggregation per symbol
- News features with 1-day lag
- Retrain models with news features
- Walk-forward re-evaluation
- Ablation: with vs without news

**Dependencies**: Phase 11 (can run in parallel after Phase 8)
**Validation**:
- News features improve log loss / Sharpe
- No leakage (strict lag enforcement)
- Sentiment quality validated

**Completion**: News integrated if valuable

---

## Phase 13: Prediction Agent (Weeks 23-24)

**Goal**: Build agent coordination layer

**Inputs**: Technical model, news model, risk engine
**Outputs**: Unified prediction agent

**Tasks**:
- Technical agent (XGBoost + SHAP)
- News agent (sentiment rules)
- Risk agent (hard constraints)
- Decision engine (weighted combination, veto, no-trade)
- Explanation generation (SHAP + model contributions)
- Natural language explanations
- Conflict detection
- Confidence-weighted position sizing

**Dependencies**: Phases 8, 11, 12
**Validation**:
- Agent produces coherent decisions
- Explanations match model inputs
- Risk veto works
- No-trade conditions trigger appropriately

**Completion**: Agent operational

---

## Phase 14: Dashboard + API (Weeks 25-26)

**Goal**: Production-ready API and dashboard

**Inputs**: All backend components
**Outputs**: Deployed API, dashboard

**Tasks**:
- FastAPI with all endpoints
- Authentication, rate limiting
- WebSocket for real-time predictions
- React/TypeScript dashboard
- Prediction explorer
- Performance charts
- Model comparison
- Drift monitoring
- Backtest viewer
- Paper trading view

**Dependencies**: Phase 11
**Validation**:
- API latency < 100ms p99
- Dashboard loads < 3s
- All endpoints functional
- Auth working
- Rate limiting enforced

**Completion**: API and dashboard deployed

---

## Phase 15: Monitoring + Retraining (Weeks 27-28)

**Goal**: Production monitoring and automated retraining

**Inputs**: Live system, drift detectors
**Outputs**: Monitoring dashboard, retraining pipeline

**Tasks**:
- Prediction drift detection (PSI, KS)
- Feature drift detection (per feature PSI)
- Performance drift (rolling metrics)
- Data quality monitoring
- Calibration monitoring
- Alerting (Slack, email, webhook)
- Retraining triggers (schedule + drift)
- Candidate training pipeline
- Shadow deployment
- Promotion workflow with approval
- Rollback procedure

**Dependencies**: Phase 14
**Validation**:
- Drift detection alerts on injected drift
- Retraining pipeline executes end-to-end
- Shadow deployment validates candidates
- Promotion requires human approval
- Rollback < 15 min

**Completion**: Full monitoring and retraining operational

---

## Summary Timeline

| Phase | Weeks | Duration | Key Deliverable |
|-------|-------|----------|-----------------|
| 0 | 1 | 1 week | Problem definition |
| 1 | 2-3 | 2 weeks | Data ingestion pipeline |
| 2 | 4 | 1 week | Clean data in TimescaleDB |
| 3 | 5-6 | 2 weeks | Feature store |
| 4 | 7 | 1 week | Labels |
| 5 | 8 | 1 week | EDA report |
| 6 | 9-10 | 2 weeks | Baseline models |
| 7 | 11-12 | 2 weeks | Classical ML models |
| 8 | 13 | 1 week | Ensemble |
| 9 | 14-15 | 2 weeks | Backtesting |
| 10 | 16 | 1 week | Walk-forward validation |
| 11 | 17-20 | 4 weeks | Paper trading |
| 12 | 21-22 | 2 weeks | News/Sentiment |
| 13 | 23-24 | 2 weeks | Prediction Agent |
| 14 | 25-26 | 2 weeks | API + Dashboard |
| 15 | 27-28 | 2 weeks | Monitoring + Retraining |
| **Total** | | **~28 weeks** | **Production system** |

---

## Parallel Tracks

After Phase 8, these can run in parallel:
- Track A: Phases 9-11 (Backtest -> Paper Trading)
- Track B: Phase 12 (News/Sentiment)
- Track C: Phase 13 (Agent) - needs Track A+B
- Track D: Phase 14 (API/Dashboard) - needs Track A
- Track E: Phase 15 (Monitoring) - needs Track D

Critical Path: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 14 -> 15
(~22 weeks minimum)
