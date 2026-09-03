# PREDIXA AI

**AI/ML Market Prediction Agent** - A research-grade system for discovering whether machine learning can identify a statistically meaningful predictive edge in equity markets.

## Vision

Build a rigorous, reproducible AI/ML system that estimates the probability of positive/negative/neutral returns for stocks over defined horizons - without claiming certainty or guaranteeing profits.

## Key Principles

- **Probabilities, not predictions**: Output calibrated probabilities (P(UP), P(DOWN), P(SIDEWAYS))
- **Scientific rigor**: Walk-forward validation, no look-ahead bias, realistic costs
- **Reproducibility**: Every experiment versioned, tracked, reproducible
- **Cost-aware**: Transaction costs, slippage, spread modeled from day one
- **Paper trading first**: Live validation before any capital allocation
- **Transparent failures**: Document negative results as carefully as successes

## System Capabilities

- Historical data ingestion (OHLCV, fundamentals, news, macro)
- 100+ features across 8 groups (price, technical, volatility, relative, regime, fundamental, news, macro)
- Label generation for multiple horizons (1, 5, 10, 20, 60 days) and thresholds
- ML pipeline: Logistic Regression -> XGBoost/LightGBM -> Ensemble
- Walk-forward validation with expanding windows and embargo gaps
- Event-driven backtesting with realistic costs
- Paper trading with immutable prediction logging
- Prediction agent coordinating technical, news, and risk models
- Model monitoring with drift detection (PSI, KS, ADWIN)
- Automated retraining with shadow deployment and human approval
- REST API + WebSocket for real-time predictions
- React/TypeScript dashboard for monitoring

## Documentation

See docs/ for complete technical documentation (31 documents).

## Quick Start

`ash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Ingest data
python scripts/ingest_data.py

# Compute features
python scripts/compute_features.py

# Generate labels
python scripts/generate_labels.py

# Train model
python scripts/train_model.py

# Run backtest
python scripts/run_backtest.py

# Start paper trading
python scripts/run_paper_trading.py
`

## Status

**Phase**: Documentation Complete
**Next**: Implementation (Phase 1: Data Collection)

## Disclaimer

This is a **research tool** for investigating whether ML can find a repeatable edge in markets. It does **not** guarantee profits. Past performance does not indicate future results. All outputs are probabilities, not certainties.
