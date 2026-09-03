# EXPERIMENT_LOG.md

## Experiment Log Template

This document tracks all experiments for reproducibility.

## Experiment Entry Template

`markdown
### Experiment: {EXPERIMENT_ID}
**Date**: {YYYY-MM-DD}
**Status**: RUNNING / COMPLETED / FAILED
**Hypothesis**: {Clear, falsifiable hypothesis}
**Research Question**: {Which of the 10 research questions}

## Configuration
- **Dataset Version**: {ds_feat_vX.Y_label_vA.B_split_...}
- **Feature Version**: {feat_vX.Y}
- **Label Version**: {label_vA.B}
- **Model**: {algorithm + key hyperparams}
- **Split Method**: {expanding/rolling}
- **Folds**: {N}
- **Embargo**: {N days}
- **Random Seed**: {fixed seed}

## Success Criteria (Pre-registered)
- Primary: {metric} {operator} {threshold}
- Secondary: {metric} {operator} {threshold}

## Results
### Walk-Forward Metrics (per fold)
| Fold | Train Period | Val Period | Test Period | Val LogLoss | Test LogLoss | Test AUC | Test ECE |
|------|--------------|------------|-------------|-------------|--------------|----------|----------|
| 1    | ...          | ...        | ...         | ...         | ...          | ...      | ...      |

### Aggregated (with 95% CI)
| Metric | Mean | Std | CI Lower | CI Upper | Target | Pass? |
|--------|------|-----|----------|----------|--------|-------|
| Log Loss | ... | ... | ... | ... | < 0.90 | Yes/No |

### Backtest (if applicable)
| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Net Sharpe | ... | > 1.0 | Yes/No |
| Max DD | ... | < 20% | Yes/No |

## Statistical Tests
- vs Random: p = ...
- vs Logistic Regression: p = ...
- vs XGBoost (if comparing): p = ...

## Conclusion
- **Decision**: ACCEPT / REJECT / ITERATE
- **Evidence**: {Summary of why}
- **Next Steps**: {What to do next}

## Artifacts
- MLflow Run ID: {run_id}
- Model Version: {model_version}
- Feature Importance: {path}
- Reliability Diagram: {path}
- Backtest Report: {path}

## Notes
{Any observations, issues, deviations from plan}
`

## Experiment History

| Exp ID | Date | Hypothesis | Model | Dataset | Result | Decision |
|--------|------|------------|-------|---------|--------|----------|
| exp_001 | 2024-01-15 | Technical features predict returns | Logistic Reg | ds_v1.0 | Log loss 1.05 | REJECT |
| exp_002 | 2024-01-20 | XGBoost beats Logistic Reg | XGBoost | ds_v1.0 | Log loss 0.87 | ACCEPT |
| exp_003 | 2024-01-25 | LightGBM beats XGBoost | LightGBM | ds_v1.1 | Log loss 0.86 | ACCEPT |
| exp_004 | 2024-02-01 | Ensemble beats single | Weighted Avg | ds_v1.2 | Log loss 0.84 | ACCEPT |
| exp_005 | 2024-02-10 | News sentiment adds value | XGBoost+News | ds_v1.3 | Log loss 0.847 | ACCEPT |
| exp_006 | 2024-02-20 | Deep learning adds value | LSTM | ds_v1.3 | Log loss 0.88 | REJECT |
| exp_007 | 2024-03-01 | Regime conditioning helps | Regime Ensemble | ds_v1.3 | Mixed | ITERATE |

## Failed Experiments (Documented)

| Exp ID | Date | Hypothesis | Why Failed | Lesson Learned |
|--------|------|------------|------------|----------------|
| exp_fail_01 | 2024-01-10 | Random forest with 1000 trees | Overfit, val loss >> train loss | Need stronger regularization |
| exp_fail_02 | 2024-01-18 | No embargo in CV | Leakage, inflated val metrics | Always use embargo |
| exp_fail_03 | 2024-02-05 | SMOTE for class balance | Created synthetic future data | Never SMOTE time series |

## Reproducibility Checklist

- [ ] Random seed fixed and recorded
- [ ] Dataset version recorded
- [ ] Feature version recorded
- [ ] Label version recorded
- [ ] Code version (git commit) recorded
- [ ] Environment (conda/pip) captured
- [ ] MLflow run created with all params/metrics
- [ ] Model artifact saved
- [ ] All metrics computed on test set only
- [ ] Statistical tests performed
- [ ] Conclusion matches pre-registered criteria
