# PROJECT_SUMMARY.md

## PREDIXA AI - Complete Technical Summary

## Project Overview

**Name**: PREDIXA AI - AI/ML Market Prediction Agent
**Type**: Research-grade quantitative ML system
**Objective**: Discover whether ML can identify a statistically meaningful, repeatable predictive edge on unseen/live market data
**Scope**: US equities (S&P 500 + liquid mid-caps), daily frequency, horizons 5/20 days
**Mode**: Research/paper trading only - NO real-money trading

## Problem Definition

Predict P(UP), P(DOWN), P(SIDEWAYS) for each stock over 5/20 trading day horizons using close-to-close returns with 2% thresholds. The system outputs calibrated probabilities, not point predictions.

## Architecture Summary

Data Sources -> Ingestion -> Validation -> Storage (TimescaleDB + Data Lake)
    -> Feature Engineering (8 groups, 101 features, strict lag enforcement)
    -> Label Generation (3-class + 2-class, configurable horizons/thresholds)
    -> Dataset Builder (walk-forward splits, expanding window, 30-day embargo)
    -> ML Training (Baseline -> Classical -> Ensemble -> optional DL)
    -> Model Registry (MLflow, versioned, lineage)
    -> Prediction Engine (feature store, calibration, confidence)
    -> Risk Engine (position, portfolio, liquidity, model uncertainty limits)
    -> Ranking Engine (probability + expected return, diversification filters)
    -> Prediction Agent (Technical + News + Risk agents -> Decision Engine)
    -> API (FastAPI) + Dashboard (React/TypeScript)
    -> Monitoring (drift detection, performance tracking, retraining triggers)

## Data Architecture

**Categories**: Historical (static), Live (streaming), Derived (features/labels), Model-generated (predictions/outcomes)
**Sources**: Polygon/Yahoo/Alpha Vantage (OHLCV), SEC/Financial APIs (fundamentals), NewsAPI/RSS (news), FRED (macro)
**Storage**: Parquet data lake (raw), TimescaleDB (validated), Feast (features), MLflow (models), PostgreSQL (predictions/trades)
**Versioning**: All data, features, labels, datasets, models versioned with content hashes

## Leakage Prevention (Critical)

- Temporal integrity: Every feature timestamp <= prediction timestamp
- No future data: Expanding windows only, no shift(-n), no global statistics
- Lag enforcement: Fundamentals 60d, News 1d, Macro 1d, Market-relative 1d
- Corporate actions: Applied at announcement date, not ex-date
- Validation: Automated leakage tests in CI/CD
- Audit trail: Every prediction logged with feature hash, model version, timestamp

## ML Strategy

**Progression**: Random -> Logistic Regression -> XGBoost/LightGBM -> Ensemble -> (DL only if justified)
**Core principle**: A more complex model must only be accepted if it demonstrates improvement on genuinely unseen data.
**Validation**: Walk-forward only (5+ folds, expanding, 30-day embargo)
**Primary metrics**: Log loss, Brier score, ECE (calibration)
**Targets**: Log loss < 0.90, ECE < 0.02, ROC-AUC > 0.58

## Ensemble

**Method**: Weighted average of calibrated probabilities (inverse validation log-loss weights)
**Models**: XGBoost (technical), XGBoost (technical+fundamental), XGBoost (technical+news), LightGBM, RF, Logistic Regression
**Calibration**: Isotonic regression on held-out calibration set, AFTER ensemble
**Diversity target**: Disagreement 15-30%, Q-statistic < 0.7

## Backtesting

**Engine**: Event-driven (not vectorized)
**Entry**: Next-day open | **Exit**: Fixed horizon
**Costs**: Commission .005/share, 10 bps spread, 5 bps square-root slippage
**Sizing**: Fixed fractional, 5% max position
**Constraints**: Max position 10%, sector 30%, gross exposure 100%, turnover 200%/yr
**Metrics**: Net Sharpe > 1.0, Max DD < 20%, Profit factor > 1.2

## Walk-Forward Validation

- Expanding window (growing training set)
- 5+ folds, 30-day embargo between train/val/test
- Per-fold HPO on validation, calibration on separate cal set
- Bootstrap 95% CIs for all metrics
- Stability: CV < 10%, no trend across folds

## Paper Trading

- Daily predictions at 16:00 ET
- Identical feature computation as training (feature store)
- Immutable prediction logging BEFORE outcome known
- Execution at next open with costs
- Automated outcome resolution
- Divergence detection vs backtest expectations

## Prediction Agent

- Technical Agent: XGBoost + SHAP explanations
- News Agent: FinBERT sentiment + rule-based signals
- Risk Agent: Hard constraints (veto power)
- Decision Engine: Confidence-weighted combination, conflict detection, no-trade conditions
- Explainability: SHAP waterfall + model contributions + natural language

## Monitoring & Retraining

**Drift Detection**: PSI (predictions/features), KS test, ADWIN (streaming), performance metrics
**Alerting**: Slack/email/webhook on thresholds
**Retraining**: Monthly schedule + trigger-based (drift, performance drop)
**Validation**: Holdout + 4-week shadow deployment
**Promotion**: Human approval required, rollback < 15 min

## Technology Stack

| Layer | Primary |
|-------|---------|
| API | FastAPI |
| Data | Polars + Pandas |
| DB | TimescaleDB + PostgreSQL |
| Cache | Redis |
| ML | XGBoost, LightGBM, Scikit-learn |
| DL | PyTorch (optional) |
| HPO | Optuna |
| Feature Store | Feast |
| Experiment Tracking | MLflow |
| Orchestration | Airflow |
| Containers | Docker + Kubernetes |
| Monitoring | Prometheus + Grafana |
| Frontend | React + TypeScript |

## Development Roadmap

15 phases over ~28 weeks:
- Phases 0-5: Foundation (data, features, labels, EDA) - 8 weeks
- Phases 6-8: Model development (baseline -> classical -> ensemble) - 5 weeks
- Phases 9-11: Validation (backtest, walk-forward, paper trading) - 7 weeks
- Phases 12-13: Enhancement (news, agent) - 4 weeks
- Phases 14-15: Production (API/dashboard, monitoring/retraining) - 4 weeks

## Success Criteria

**Stage 1**: Clean data, features, labels, EDA complete
**Stage 2**: Model beats baselines on walk-forward (log loss < 0.90, ECE < 0.02)
**Stage 3**: Net Sharpe > 1.0 after costs, paper trading matches backtest
**Stage 4**: Agent coherent, explainable, API/dashboard operational
**Stage 5**: Monitoring detects drift, retraining pipeline validated

## Risks & Limitations

- No guaranteed prediction - markets are adaptive
- Overfitting risk - mitigated by walk-forward, regularization
- Transaction costs - modeled from day one
- Survivorship bias - tracked with delisting dates
- Regime changes - monitored via drift detection
- Model drift - continuous monitoring + retraining
- False confidence - calibrated probabilities, confidence separate

## Documentation Package

31 core documents + 12 summary documents covering all aspects from problem definition through production deployment.