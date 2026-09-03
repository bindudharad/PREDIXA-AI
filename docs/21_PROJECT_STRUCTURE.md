# 21_PROJECT_STRUCTURE.md

## Project Folder Structure

This document defines the professional folder structure for the PREDIXA AI project.

## Root Structure

`
market-prediction-agent/
│
├── data/                    # Data storage (not in git)
│   ├── raw/                 # Raw data from providers
│   │   ├── ohlcv/
│   │   ├── fundamentals/
│   │   ├── news/
│   │   └── macro/
│   ├── processed/           # Cleaned/validated data
│   │   ├── ohlcv_adjusted/
│   │   └── corporate_actions/
│   ├── features/            # Computed features (offline store)
│   │   └── feat_v1.3/
│   ├── labels/              # Generated labels
│   │   └── label_v2.1/
│   └── datasets/            # Train/val/test splits
│       └── ds_feat_v1.3_label_v2.1_split_expanding_a1b2c3d4/
│
├── notebooks/               # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_model_comparison.ipynb
│   ├── 04_backtest_analysis.ipynb
│   └── 05_drift_analysis.ipynb
│
├── src/                     # Main source code
│   ├── __init__.py
│   ├── config.py
│   │
│   ├── ingestion/           # Data ingestion
│   │   ├── __init__.py
│   │   ├── ohlcv.py
│   │   ├── fundamentals.py
│   │   ├── news.py
│   │   ├── macro.py
│   │   └── corporate_actions.py
│   │
│   ├── validation/          # Data validation
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── range_checks.py
│   │   ├── continuity.py
│   │   ├── outliers.py
│   │   └── quality_report.py
│   │
│   ├── preprocessing/       # Data cleaning
│   │   ├── __init__.py
│   │   ├── adjust_prices.py
│   │   ├── handle_missing.py
│   │   ├── handle_duplicates.py
│   │   └── survivorship.py
│   │
│   ├── features/            # Feature engineering
│   │   ├── __init__.py
│   │   ├── price.py
│   │   ├── technical.py
│   │   ├── volatility.py
│   │   ├── market_relative.py
│   │   ├── regime.py
│   │   ├── fundamental.py
│   │   ├── news.py
│   │   ├── macro.py
│   │   └── pipeline.py
│   │
│   ├── labels/              # Label generation
│   │   ├── __init__.py
│   │   ├── returns.py
│   │   ├── classification.py
│   │   └── pipeline.py
│   │
│   ├── datasets/            # Dataset building
│   │   ├── __init__.py
│   │   ├── splits.py
│   │   ├── builder.py
│   │   └── versioning.py
│   │
│   ├── models/              # Model definitions
│   │   ├── __init__.py
│   │   ├── baseline.py
│   │   ├── xgboost_model.py
│   │   ├── lightgbm_model.py
│   │   ├── random_forest.py
│   │   ├── lstm.py
│   │   ├── transformer.py
│   │   └── registry.py
│   │
│   ├── training/            # Training pipeline
│   │   ├── __init__.py
│   │   ├── trainer.py
│   │   ├── hpo.py
│   │   ├── calibration.py
│   │   └── walkforward.py
│   │
│   ├── evaluation/          # Model evaluation
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── calibration.py
│   │   ├── statistical_tests.py
│   │   └── regime_analysis.py
│   │
│   ├── ensemble/            # Ensemble methods
│   │   ├── __init__.py
│   │   ├── weighted_avg.py
│   │   ├── stacking.py
│   │   └── regime_conditioned.py
│   │
│   ├── backtesting/         # Backtesting engine
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── costs.py
│   │   ├── sizing.py
│   │   ├── constraints.py
│   │   └── metrics.py
│   │
│   ├── prediction/          # Prediction engine
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── ranking.py
│   │   └── logging.py
│   │
│   ├── agents/              # Prediction agent
│   │   ├── __init__.py
│   │   ├── technical_agent.py
│   │   ├── news_agent.py
│   │   ├── risk_agent.py
│   │   ├── decision_engine.py
│   │   └── explanation.py
│   │
│   ├── risk/                # Risk engine
│   │   ├── __init__.py
│   │   ├── position_risk.py
│   │   ├── portfolio_risk.py
│   │   ├── liquidity.py
│   │   └── limits.py
│   │
│   ├── monitoring/          # Model monitoring
│   │   ├── __init__.py
│   │   ├── drift.py
│   │   ├── performance.py
│   │   ├── data_quality.py
│   │   ├── alerts.py
│   │   └── retraining.py
│   │
│   ├── paper_trading/       # Paper trading
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── portfolio.py
│   │   ├── execution.py
│   │   └── reconciliation.py
│   │
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── dates.py
│       ├── math.py
│       ├── logging.py
│       └── decorators.py
│
├── api/                     # API layer
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── stocks.py
│   │   ├── predictions.py
│   │   ├── backtest.py
│   │   ├── performance.py
│   │   ├── models.py
│   │   ├── paper_trading.py
│   │   └── health.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── predictions.py
│   │   ├── backtest.py
│   │   └── models.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── rate_limit.py
│   │   └── logging.py
│   └── websocket/
│       ├── __init__.py
│       └── predictions.py
│
├── dashboard/               # Frontend dashboard
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   └── public/
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_features.py
│   │   ├── test_labels.py
│   │   ├── test_models.py
│   │   └── test_backtest.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   ├── test_api.py
│   │   └── test_paper_trading.py
│   └── fixtures/
│
├── configs/                 # Configuration files
│   ├── base.yaml
│   ├── development.yaml
│   ├── production.yaml
│   ├── model_xgboost.yaml
│   ├── model_lightgbm.yaml
│   ├── backtest.yaml
│   ├── paper_trading.yaml
│   └── monitoring.yaml
│
├── scripts/                 # Operational scripts
│   ├── ingest_data.py
│   ├── compute_features.py
│   ├── generate_labels.py
│   ├── train_model.py
│   ├── run_backtest.py
│   ├── run_prediction.py
│   ├── run_paper_trading.py
│   ├── monitor_drift.py
│   ├── retrain_model.py
│   └── promote_model.py
│
├── experiments/             # Experiment tracking (MLflow)
│   └── mlruns/
│
├── models/                  # Model artifacts (not in git)
│   ├── model_xgboost_v1.2.0/
│   │   ├── model.pkl
│   │   ├── config.yaml
│   │   ├── metrics.json
│   │   └── feature_names.json
│   └── model_lgbm_v1.1.0/
│
├── logs/                    # Application logs (not in git)
│   ├── application/
│   ├── predictions/
│   ├── drift/
│   └── api/
│
├── docs/                    # Documentation
│   ├── 01_PROJECT_OVERVIEW.md
│   ├── 02_REQUIREMENTS.md
│   ├── ...
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── MODEL_CARD.md
│   ├── EXPERIMENT_LOG.md
│   ├── BACKTESTING_GUIDE.md
│   ├── LIVE_PREDICTION_GUIDE.md
│   ├── AGENT_DESIGN.md
│   ├── API_DOCUMENTATION.md
│   ├── DEVELOPMENT_ROADMAP.md
│   └── RISK_AND_LIMITATIONS.md
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── kubernetes/
│   ├── base/
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── helm/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── retraining.yml
│
├── .gitignore
├── .dockerignore
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
└── pytest.ini
`

## Key Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Reproducibility**: Versioned data, features, labels, models
3. **Testability**: Clear module boundaries enable unit testing
4. **Scalability**: Horizontal scaling via worker modules
5. **Observability**: Logging, metrics, tracing built-in
6. **Security**: Config separate from code, no secrets in repo

## Module Dependencies

`
ingestion -> validation -> preprocessing -> features -> labels -> datasets
                                                                      -> training -> models -> registry
                                                                      -> evaluation
                                                                      -> backtesting
                                                                      -> prediction -> agents -> paper_trading
                                                                      -> monitoring
`

## Configuration Management

- Base config in configs/base.yaml
- Environment overrides in configs/{env}.yaml
- Model-specific configs in configs/model_{name}.yaml
- Loaded via src/config.py with Pydantic validation
