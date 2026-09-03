# 28_EXPERIMENT_PLAN.md

## Experiment Plan

This document designs experiments to answer key research questions.

## Research Questions

### Experiment 1: Can technical features predict future returns?
- **Hypothesis**: Price/volume features contain predictive signal
- **Method**: Train Logistic Regression on technical features only
- **Validation**: Walk-forward (5 folds, expanding, 30-day embargo)
- **Success**: Log loss < 1.0, ROC-AUC > 0.55, ECE < 0.05
- **Failure criterion**: No better than random on test periods

### Experiment 2: Does XGBoost outperform Logistic Regression?
- **Hypothesis**: Non-linear model captures interactions
- **Method**: Same data, XGBoost with HPO vs Logistic Regression
- **Validation**: Walk-forward, paired bootstrap test
- **Success**: XGBoost log loss significantly lower (p < 0.05)
- **Failure**: No significant difference or XGBoost worse

### Experiment 3: Does LightGBM outperform XGBoost?
- **Hypothesis**: Leaf-wise growth better for this data
- **Method**: Same setup, LightGBM vs XGBoost
- **Validation**: Walk-forward, paired test
- **Success**: LightGBM significantly better
- **Failure**: No difference or XGBoost better

### Experiment 4: Does deep learning add value?
- **Hypothesis**: Temporal patterns captured by LSTM/Transformer
- **Method**: LSTM/GRU on feature sequences vs best classical
- **Validation**: Walk-forward, strict criteria
- **Success**: Beats ensemble on ALL: log loss, calibration, stability
- **Failure**: Any criterion fails (default: reject DL)

### Experiment 5: Does news sentiment improve predictions?
- **Hypothesis**: Sentiment adds orthogonal information
- **Method**: Ablation - models with vs without news features
- **Validation**: Walk-forward, same splits
- **Success**: Significant improvement in log loss AND trading metrics
- **Failure**: No improvement or degradation

### Experiment 6: Does market-regime detection improve performance?
- **Hypothesis**: Regime-conditioned models adapt better
- **Method**: Regime-conditioned ensemble vs global ensemble
- **Validation**: Walk-forward, regime-conditional metrics
- **Success**: Better in at least 2 regimes, not worse in others
- **Failure**: No consistent improvement

### Experiment 7: Does ensemble outperform individual models?
- **Hypothesis**: Diversity reduces variance
- **Method**: Weighted average/stacking vs best single model
- **Validation**: Walk-forward, test periods
- **Success**: Ensemble significantly better on test
- **Failure**: No improvement or single model better

### Experiment 8: Does edge survive transaction costs?
- **Hypothesis**: Predictive edge > cost drag
- **Method**: Backtest with realistic costs (30-40 bps round-trip)
- **Validation**: Walk-forward backtest
- **Success**: Net Sharpe > 1.0, profit factor > 1.2
- **Failure**: Gross edge exists but net negative

### Experiment 9: Does performance survive walk-forward testing?
- **Hypothesis**: Edge is robust across time periods
- **Method**: 5+ non-overlapping test periods
- **Validation**: Stability metrics (CV < 10%, no trend)
- **Success**: Consistent positive metrics across all folds
- **Failure**: High variance, negative periods, trend downward

### Experiment 10: Does performance remain stable in live paper trading?
- **Hypothesis**: Live performance matches backtest expectations
- **Method**: 3+ months paper trading
- **Validation**: Divergence detection (z-score < 2)
- **Success**: Live metrics within backtest CIs
- **Failure**: Significant divergence (z > 2)

## Experiment Framework Requirements

The framework MUST allow the model to fail:
- No cherry-picking test periods
- No metric selection after seeing results
- All experiments pre-registered
- Failed experiments documented as carefully as successes
- Random seed fixed per experiment
- Full reproducibility (code + data + config versions)

## Experiment Template

`markdown
# Experiment: {Name}

## Hypothesis
{Clear, falsifiable hypothesis}

## Method
{Exact methodology, data, models, validation}

## Success Criteria
{Pre-defined quantitative thresholds}

## Failure Criteria
{Pre-defined conditions for rejection}

## Results
{All metrics, CIs, statistical tests}

## Conclusion
{Accept/Reject hypothesis with evidence}

## Artifacts
{Model versions, dataset versions, logs}
`

## Experiment Schedule

| Experiment | Phase | Duration | Depends On |
|------------|-------|----------|------------|
| 1: Technical features | 6 | 1 week | Phase 3-4 |
| 2: XGBoost vs LR | 7 | 1 week | Exp 1 |
| 3: LightGBM vs XGB | 7 | 1 week | Exp 2 |
| 4: Deep Learning | 7+ | 2 weeks | Exp 2-3 |
| 5: News sentiment | 12 | 1 week | Phase 12 |
| 6: Regime detection | 8 | 1 week | Phase 3 |
| 7: Ensemble | 8 | 1 week | Exp 2-3 |
| 8: Costs survival | 9 | 1 week | Phase 8 |
| 9: Walk-forward | 10 | 1 week | Phase 9 |
| 10: Paper trading | 11 | 12 weeks | Phase 10 |

## Pre-registration

All experiments pre-registered in MLflow with:
- Experiment name and hypothesis
- Success/failure criteria
- Dataset version
- Config hashes
- Random seeds

## Reporting

Every experiment produces:
1. MLflow run with all params/metrics/artifacts
2. Experiment report (markdown)
3. Decision: proceed to next / iterate / stop
4. Updated experiment log
