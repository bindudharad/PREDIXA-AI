# 30_SUCCESS_CRITERIA.md

## Success Criteria

This document defines measurable success criteria for each stage.

## Stage 1: Research Foundation (Phases 1-5)

### Data Pipeline
- [ ] Ingests 5+ years clean OHLCV for 500+ symbols
- [ ] Corporate actions correctly applied (splits, dividends, M&A)
- [ ] Survivorship tracked: delisting dates and reasons recorded
- [ ] Data quality reports generated per ingestion run
- [ ] Multi-provider failover working
- [ ] Incremental daily updates < 30 min

### Feature Engineering
- [ ] 100+ features across 8 groups computed
- [ ] Zero look-ahead bias (automated tests pass)
- [ ] Feature versioning with code+config hash
- [ ] Feature store online = offline consistency verified
- [ ] Lag enforcement: fundamentals 60d, news 1d, macro 1d

### Label Generation
- [ ] 3-class (UP/DOWN/SIDEWAYS) and 2-class labels
- [ ] Configurable horizons: 1, 5, 10, 20, 60 days
- [ ] Configurable thresholds: 1%, 1.5%, 2%, 2.5%, 3%
- [ ] Entry/exit timing clearly defined (close-to-close)
- [ ] Label versioning with config hash

### EDA
- [ ] Feature distributions documented
- [ ] Label distributions per horizon/threshold
- [ ] Feature-target correlations analyzed
- [ ] Regime-conditional analysis complete
- [ ] Feature stability across time assessed

**Stage 1 Gate**: All above complete, documented, reproducible

---

## Stage 2: Model Development (Phases 6-8)

### Baseline Models
- [ ] Logistic Regression trained and evaluated via walk-forward
- [ ] Random Forest baseline trained
- [ ] Random prediction baseline documented
- [ ] Buy-and-hold benchmark documented
- [ ] **Logistic Regression beats Random on walk-forward test (p < 0.05)**
- [ ] Log loss < 1.10, Brier < 0.40, ECE < 0.05

### Classical ML
- [ ] XGBoost trained with Optuna HPO (temporal CV)
- [ ] LightGBM trained with Optuna HPO
- [ ] **XGBoost/LightGBM beat Logistic Regression (p < 0.05)**
- [ ] Log loss < 0.90, Brier < 0.30, ECE < 0.02
- [ ] ROC-AUC > 0.58, Accuracy > 42%
- [ ] Feature importance stable across folds (Spearman > 0.7)
- [ ] Calibration: ECE < 0.02, reliability diagram near diagonal

### Ensemble
- [ ] Weighted average ensemble (inverse validation log-loss weights)
- [ ] Stacking meta-learner evaluated
- [ ] **Ensemble beats best single model on test (p < 0.05)**
- [ ] Calibration maintained or improved
- [ ] Model contributions traceable

### Deep Learning (Optional)
- [ ] Only if classical ML shows consistent edge
- [ ] LSTM/GRU trained on sequences
- [ ] **Beats ensemble on ALL: log loss, calibration, stability, latency**
- [ ] If any criterion fails: reject DL, stay with ensemble

**Stage 2 Gate**: Best model (ensemble or single) passes all thresholds on walk-forward test

---

## Stage 3: Validation & Deployment (Phases 9-11)

### Backtesting
- [ ] Event-driven backtest engine (not vectorized)
- [ ] Realistic costs: commission, spread, square-root slippage
- [ ] Position sizing and portfolio constraints enforced
- [ ] Walk-forward backtest (same folds as ML validation)
- [ ] **Net Sharpe > 1.0 after all costs**
- [ ] Max drawdown < 20%
- [ ] Profit factor > 1.2
- [ ] Win rate > 45%
- [ ] Expectancy > 0
- [ ] Cost drag < 50 bps/year
- [ ] Turnover < 200% annually

### Walk-Forward Validation
- [ ] 5+ non-overlapping test periods
- [ ] Expanding window with 30-day embargo
- [ ] Bootstrap 95% CIs for all metrics
- [ ] Stability: CV < 10% across folds, no downward trend
- [ ] Regime-conditional performance reported
- [ ] **Consistent edge across 3+ test periods**
- [ ] Statistical significance vs benchmarks (random, momentum, buy-hold)

### Paper Trading
- [ ] Live predictions at 16:00 ET daily
- [ ] Feature computation identical to training (feature store)
- [ ] Immutable prediction logging (pre-outcome)
- [ ] Paper execution at next open + costs
- [ ] Outcome resolution automated
- [ ] 3+ months continuous operation
- [ ] **Live metrics within backtest 95% CIs (z-score < 2)**
- [ ] No critical drift alerts
- [ ] Divergence detection working

**Stage 3 Gate**: Paper trading validates backtest expectations

---

## Stage 4: Agent & Explainability (Phases 12-13)

### News/Sentiment (If Valuable)
- [ ] News ingestion from multiple sources
- [ ] Entity recognition + sentiment classification
- [ ] Features with strict 1-day lag
- [ ] Ablation shows significant improvement
- [ ] If no improvement: document and exclude

### Prediction Agent
- [ ] Technical agent (XGBoost + SHAP)
- [ ] News agent (sentiment rules)
- [ ] Risk agent (hard constraints, veto power)
- [ ] Decision engine (weighted combination, conflict resolution)
- [ ] No-trade conditions (low confidence, conflict, risk veto)
- [ ] Explanations: SHAP + model contributions + natural language
- [ ] Explanations reflect actual model inputs (no hallucination)

### Dashboard/API
- [ ] REST API: predictions, performance, models, health
- [ ] WebSocket for real-time updates
- [ ] Authentication + rate limiting
- [ ] Dashboard: predictions, performance, drift, backtests
- [ ] API latency < 100ms p99
- [ ] Dashboard load < 3s

**Stage 4 Gate**: Agent produces coherent, explainable decisions; API/dashboard operational

---

## Stage 5: Monitoring & Retraining (Phases 14-15)

### Monitoring
- [ ] Prediction drift (PSI, KS) detected
- [ ] Feature drift (per-feature PSI) detected
- [ ] Performance drift (rolling metrics) detected
- [ ] Calibration drift (ECE) detected
- [ ] Data quality monitoring (freshness, completeness)
- [ ] Alerting: Slack/email/webhook on thresholds
- [ ] Dashboard shows all drift metrics

### Retraining
- [ ] Monthly scheduled retraining
- [ ] Trigger-based retraining (drift, performance drop)
- [ ] Candidate training on updated data
- [ ] Holdout validation vs production
- [ ] 4-week shadow deployment
- [ ] Promotion requires human approval
- [ ] Rollback < 15 minutes
- [ ] Model versioning with full lineage

**Stage 5 Gate**: Full monitoring operational, retraining pipeline validated

---

## Overall Success Criteria (Project Level)

### Primary (Must Have)
1. **Beats random baseline** on walk-forward test (log loss, statistical significance)
2. **Stable out-of-sample performance** across 3+ non-overlapping periods
3. **Good probability calibration** (ECE < 0.02, Brier < 0.25)
4. **Positive expectancy** after realistic transaction costs
5. **Robust across market regimes** (not just bull market)
6. **No significant data leakage** (automated tests pass)
7. **Reproducible results** (fixed seeds, versioned everything)

### Secondary (Should Have)
1. **Beats simple benchmarks** (momentum, SMA, buy-hold) on risk-adjusted basis
2. **Ensemble improves** over best single model
3. **News sentiment adds value** (if integrated)
4. **Agent explanations** are accurate and useful
5. **Paper trading** matches backtest within confidence intervals

### Stretch (Nice to Have)
1. **Deep learning adds value** (if justified)
2. **Regime-conditioned models** improve performance
3. **Sub-5% max drawdown** in paper trading
4. **Sharpe > 2.0** net of costs

---

## Acceptance Criteria per Stage

| Stage | Primary Metric | Threshold | Must Pass |
|-------|---------------|-----------|-----------|
| 1 | Data quality | Zero critical issues | Yes |
| 2 | Log loss (walk-forward) | < 0.90 | Yes |
| 2 | ECE | < 0.02 | Yes |
| 3 | Net Sharpe | > 1.0 | Yes |
| 3 | Max DD | < 20% | Yes |
| 3 | Live vs backtest | z-score < 2 | Yes |
| 4 | Agent coherence | No logical conflicts | Yes |
| 5 | Drift detection | Alerts on injected drift | Yes |

---

## Failure Definitions

The project should conclude (or pivot) if:

1. **Stage 1**: Cannot get clean data for 500+ symbols over 5+ years
2. **Stage 2**: No model beats Logistic Regression on walk-forward after 3 algorithm attempts
3. **Stage 2**: Best model has ECE > 0.05 (poor calibration) despite attempts
4. **Stage 3**: No strategy achieves Net Sharpe > 1.0 after costs on walk-forward
5. **Stage 3**: Paper trading shows significant divergence (z > 2) persistently
6. **Any stage**: Data leakage detected that invalidates results

**Negative results are valuable** - document thoroughly and publish.
