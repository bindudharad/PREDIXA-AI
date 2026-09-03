# 20_API_DESIGN.md

API Design Document

Base URL: https://api.predixa.ai/v1

Authentication: API Key or JWT

Endpoints:
- GET /stocks
- GET /stocks/{symbol}
- GET /market/prices/{symbol}
- GET /market/indices
- GET /predictions
- GET /predictions/{symbol}
- POST /predict
- POST /backtest
- GET /backtest/{id}
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

Error codes: 400, 401, 403, 404, 429, 500, 503

WebSocket: /ws/predictions, /ws/paper-trading/portfolio

Rate limiting: 1000 req/min default