# API_DOCUMENTATION.md

API Documentation - OpenAPI Ready

Base URL: https://api.predixa.ai/v1

Authentication: API Key or JWT

Rate Limiting: 1000 req/min default

Endpoints:
- GET /stocks
- GET /stocks/{symbol}
- GET /market/prices/{symbol}
- GET /market/indices
- GET /predictions
- GET /predictions/{symbol}
- POST /predict
- POST /backtest
- GET /backtest/{backtest_id}
- GET /performance
- GET /performance/compare
- GET /models
- GET /models/{model_id}
- POST /models/{model_id}/promote
- POST /models/{model_id}/demote
- GET /paper-trading/portfolio
- GET /paper-trading/trades
- GET /health
- GET /health/ready
- GET /health/live
- GET /ws/predictions
- GET /ws/paper-trading/portfolio

Object schemas: Prediction, BacktestResult, Model, Trade, Portfolio