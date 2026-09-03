# 18_RETRAINING_STRATEGY.md

## Retraining Strategy

This document defines when and how models are retrained, validated, and deployed.

## Retraining Triggers

### 1. Scheduled Retraining
- Monthly: Full retrain with updated data
- Quarterly: Architecture review + retrain
- Configuration-driven, not performance-driven

### 2. Trigger-Based Retraining
- Performance degradation detected (log loss increase > 10%)
- Feature drift detected (PSI > 0.2 on key features)
- Prediction drift detected (PSI > 0.25)
- Calibration drift (ECE > 0.05)
- Market regime change detected

### 3. Manual Retraining
- New feature availability
- New data source
- Fundamental market structure change
- Regulatory changes

## Retraining Process

`mermaid
flowchart TD
    A[Trigger] --> B[Data Preparation]
    B --> C[Feature Engineering]
    C --> D[Label Generation]
    D --> E[Dataset Build]
    E --> F[Train Candidate Model]
    F --> G[Validation on Holdout]
    G --> H{Better than Production?}
    H -->|No| I[Reject Candidate]
    H -->|Yes| J[Shadow Deployment]
    J --> K[Shadow Validation]
    K --> L{Better in Shadow?}
    L -->|No| I
    L -->|Yes| M[Promote to Production]
    M --> N[Archive Old Model]
`

## Dataset Window for Retraining

### Expanding Window (Default)
- Use all available history up to retraining date
- More data = better model (generally)
- Risk: Includes stale regimes

### Rolling Window (Alternative)
- Fixed window (e.g., last 3 years)
- Adapts faster to regime changes
- Risk: Less data, higher variance

### Recommended: Expanding with Regime Weighting
- Expanding window
- Weight recent samples higher
- Explicit regime detection and conditioning

## Model Versioning

`
model_xgboost_v1.2.0
├── model.pkl
├── config.yaml
├── metrics.json
├── feature_version: feat_v1.3
├── label_version: label_v2.1
├── dataset_version: ds_feat_v1.3_label_v2.1_split_expanding_a1b2c3d4
├── training_period: 2015-01-01 to 2024-01-15
├── validation_period: 2024-01-16 to 2024-03-15
├── test_period: 2024-03-16 to 2024-05-15
├── hyperparameters: {...}
├── metrics: {log_loss: 0.85, ece: 0.018, roc_auc: 0.59}
└── deployment_status: candidate / shadow / production / archived
`

## Validation Protocol

### Holdout Validation
- Recent 3 months as holdout (not used in training)
- Compare candidate vs production on holdout
- Metrics: Log loss, ECE, ROC-AUC, calibration

### Shadow Deployment
- Run candidate in parallel with production
- Same inputs, log both predictions
- Duration: 2-4 weeks
- Compare on actual outcomes
- Only promote if statistically better

### A/B Testing (Alternative)
- Split traffic 50/50
- Compare live performance
- Requires sufficient volume

## Approval Gates

| Gate | Criteria | Decision |
|------|----------|----------|
| Training Complete | No errors, metrics computed | Auto-pass |
| Validation | Candidate log loss < Production log loss - margin | Data scientist |
| Shadow | Candidate beats production on live data (stat sig) | Data scientist + PM |
| Promotion | All gates passed, rollback plan ready | PM approval |

## Rollback Procedure

1. Detect issue (performance drop, errors, anomalies)
2. Immediate: Switch traffic to previous production model
3. Investigate: Root cause analysis
4. Fix: Retrain with corrected pipeline
5. Re-validate: Full validation protocol
6. Re-deploy: Only after all gates pass

Rollback must complete within 15 minutes of detection.

## Retraining Frequency Guidelines

| Scenario | Frequency | Window |
|----------|-----------|--------|
| Stable regime | Monthly | Expanding |
| Volatile regime | Bi-weekly | Expanding (weighted) |
| Major regime change | Immediate trigger | Rolling (1-2 years) |
| New data source | Immediate trigger | Expanding |

## Configuration

`python
@dataclass
class RetrainingConfig:
    schedule: str = 'monthly'  # monthly, quarterly, none
    trigger_performance: bool = True
    trigger_drift: bool = True
    perf_threshold: float = 0.10  # 10% log loss increase
    feature_drift_threshold: float = 0.20
    pred_drift_threshold: float = 0.25
    calibration_threshold: float = 0.05
    holdout_months: int = 3
    shadow_weeks: int = 4
    min_improvement: float = 0.02  # 2% relative log loss improvement
    rollback_timeout_min: int = 15
`

## Summary

| Aspect | Decision |
|--------|----------|
| Primary Trigger | Monthly schedule + performance/drift triggers |
| Dataset Window | Expanding (weighted) |
| Validation | Holdout + 4-week shadow |
| Promotion | Human approval required |
| Rollback | < 15 min, automatic on alert |
| Versioning | Semantic + metadata |
