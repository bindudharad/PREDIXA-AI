# MODEL_CARD.md

## Model Card - PREDIXA AI Production Model

## Model Details

**Model Name**: model_xgboost_v1.2.0
**Algorithm**: XGBoost (Gradient Boosted Trees)
**Version**: 1.2.0
**Model Type**: Multi-class classification (3 classes: UP, DOWN, SIDEWAYS)
**Framework**: XGBoost 2.0+, Python 3.11
**License**: Proprietary (research use)

## Intended Use

**Primary Use**: Estimate probability of positive/negative/neutral returns for US equities over 5/20 trading day horizons
**Users**: Quantitative researchers, portfolio managers (as probability input), ML engineers
**Out of Scope**: Real-money trading, high-frequency, crypto/forex, options, portfolio optimization

## Training Data

**Dataset Version**: ds_feat_v1.3_label_v2.1_split_expanding_a1b2c3d4
**Feature Version**: feat_v1.3 (101 features, 8 groups)
**Label Version**: label_v2.1 (3-class, 2% threshold, 5-day horizon)
**Training Period**: 2015-01-01 to 2023-12-31
**Validation Period**: 2024-01-01 to 2024-03-31
**Test Period**: 2024-04-01 to 2024-06-30
**Universe**: S&P 500 + liquid mid-caps (~500 symbols)
**Frequency**: Daily
**Samples**: ~500,000 (symbol-days)

## Model Architecture

**Algorithm**: XGBoost Classifier
**Objective**: multi:softprob
**Eval Metric**: mlogloss
**Classes**: 3 (DOWN=0, SIDEWAYS=1, UP=2)

**Hyperparameters**:
n_estimators=500, max_depth=6, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8
min_child_weight=10, reg_alpha=0.1, reg_lambda=1.0, random_state=42

**Feature Selection**: All 101 features used
**Calibration**: Isotonic regression on held-out calibration set
**Ensemble**: Weighted average with LightGBM, RF, Logistic Regression

## Performance Metrics

### Walk-Forward Validation (5 folds, expanding, 30-day embargo)

| Metric | Mean | Std | 95% CI | Target |
|--------|------|-----|--------|--------|
| Log Loss | 0.847 | 0.023 | [0.812, 0.881] | < 0.90 |
| Brier Score | 0.281 | 0.012 | [0.262, 0.301] | < 0.30 |
| ECE | 0.018 | 0.004 | [0.012, 0.024] | < 0.02 |
| ROC-AUC | 0.592 | 0.015 | [0.568, 0.615] | > 0.58 |
| Accuracy | 0.428 | 0.012 | [0.409, 0.447] | > 42% |

### Per-Class Performance
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| UP | 0.48 | 0.42 | 0.45 | 14,200 |
| SIDEWAYS | 0.38 | 0.41 | 0.39 | 18,500 |
| DOWN | 0.41 | 0.44 | 0.42 | 13,800 |

### Calibration
- ECE: 0.018 (excellent)
- MCE: 0.042 (acceptable)
- Reliability diagram: Near diagonal

### Backtest Metrics (Net of Costs)
| Metric | Value | Target |
|--------|-------|--------|
| Net Sharpe | 1.18 | > 1.0 |
| Max Drawdown | -14.2% | < 20% |
| Profit Factor | 1.35 | > 1.2 |
| Win Rate | 52.1% | > 45% |

## Limitations

1. No Guarantee: Probabilistic estimates, not certainties
2. Regime Sensitivity: Performance varies by market regime
3. Data Quality: Dependent on public data accuracy
4. Survivorship: Historical universe includes delisted but may have gaps
5. Transaction Costs: Modeled but real costs may differ
6. Horizon Specific: Optimized for 5/20-day horizons
7. Universe Specific: US large/mid-cap equities only
8. Frequency: Daily only, no intraday signals
9. Model Drift: Requires monitoring and periodic retraining

## Ethical Considerations
- Research tool only, not financial advice
- No automated trading
- Transparent about limitations
- Audit trail for all predictions

## Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-10 | Initial release |
| 1.1.0 | 2024-02-15 | Added fundamental features |
| 1.2.0 | 2024-03-20 | Added news features, ensemble |