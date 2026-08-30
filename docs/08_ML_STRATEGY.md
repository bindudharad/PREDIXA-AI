# 08_ML_STRATEGY.md

## Machine Learning Strategy

This document defines the model progression from baseline through classical ML to deep learning, with explicit criteria for advancing to more complex models.

## Core Principle

> A more complex model must only be accepted if it demonstrates improvement on genuinely unseen data.

This is the single most important rule. No exceptions.

## Model Progression Path

`mermaid
flowchart LR
    B[Baseline
Logistic Regression
Random Prediction
Buy & Hold] --> C[Classical ML
Random Forest
XGBoost
LightGBM]
    C --> D{Significant
Improvement?}
    D -->|No| C
    D -->|Yes| E[Ensemble
Stacking
Weighted Avg
Meta-Model]
    E --> F{Significant
Improvement?}
    F -->|No| E
    F -->|Yes| G[Deep Learning
LSTM/GRU
Temporal CNN
Transformer]
    G --> H{Significant
Improvement?}
    H -->|No| G
    H -->|Yes| I[Production
Candidate]
`

## Phase 1: Baselines (Mandatory First Step)

Before any ML model, establish these baselines:

### 1.1 Random Prediction
- Predict class probabilities uniformly (33%/33%/33% for 3-class)
- Purpose: Sanity check - any model must beat this

### 1.2 Buy-and-Hold Benchmark
- Always predict UP (or market direction)
- Purpose: Passive benchmark - active model must beat after costs

### 1.3 Logistic Regression (with Regularization)
`python
# Baseline model specification
LogisticRegression(
    penalty='l2',
    C=1.0,  # Regularization strength
    solver='lbfgs',
    max_iter=1000,
    class_weight='balanced',  # Handle class imbalance
    random_state=42,
    multi_class='multinomial'  # For 3-class
)
`
- Features: All engineered features (no selection)
- Purpose: Linear baseline - non-linear models must beat this

### 1.4 Naive Persistence
- Predict same as last period return direction
- Purpose: Minimum temporal baseline

### Baseline Acceptance Criteria
| Metric | Random | Logistic Regression |
|--------|--------|---------------------|
| Accuracy (3-class) | ~33% | > 38% |
| Log Loss | ~1.099 | < 1.0 |
| Brier Score | ~0.444 | < 0.4 |
| ROC-AUC (OvR) | 0.5 | > 0.55 |

If Logistic Regression does not beat Random on walk-forward test -> STOP. Re-examine features/labels.

---

## Phase 2: Classical ML (Primary Focus)

### 2.1 Random Forest
`python
RandomForestClassifier(
    n_estimators=500,
    max_depth=10,  # Prevent overfitting
    min_samples_split=50,
    min_samples_leaf=20,
    max_features='sqrt',
    class_weight='balanced_subsample',
    random_state=42,
    n_jobs=-1
)
`
Advantages: Handles non-linearity, robust to outliers, feature importance, handles NaN
Disadvantages: Many trees = slow inference, limited extrapolation, correlation bias
Expected Compute: ~30 sec training on 500k samples, 100 features

### 2.2 XGBoost (Primary Classical Model)
`python
XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=10,
    reg_alpha=0.1,
    reg_lambda=1.0,
    scale_pos_weight=1,  # Adjusted per class
    objective='multi:softprob',
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1,
    early_stopping_rounds=50
)
`
Advantages: State-of-the-art tabular, handles missing, fast inference, built-in regularization
Disadvantages: Many hyperparameters, can overfit if not tuned, sequential training
Expected Compute: ~60 sec training on 500k samples, 100 features
Primary Model for v1

### 2.3 LightGBM (Alternative/Ensemble Partner)
`python
LGBMClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.03,
    num_leaves=31,
    min_child_samples=50,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    class_weight='balanced',
    objective='multiclass',
    metric='multi_logloss',
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
`
Advantages: Faster training, better memory, handles categorical natively
Disadvantages: Can overfit on small data, leaf-wise growth needs care
Use: Ensemble partner, ablation study vs XGBoost

### 2.4 CatBoost (Optional)
- Excellent for categorical features
- Ordered boosting reduces overfitting
- v1: Not primary (no categorical features in v1), reserve for v2

### Classical ML Acceptance Criteria (vs Logistic Regression)
| Metric | Minimum Improvement | Target |
|--------|---------------------|--------|
| Log Loss | -0.05 (absolute) | < 0.85 |
| Brier Score | -0.03 (absolute) | < 0.35 |
| ROC-AUC (macro) | +0.03 | > 0.58 |
| Accuracy | +2% | > 40% |
| Calibration (ECE) | Better | < 0.05 |

All metrics on OUT-OF-SAMPLE walk-forward test periods. No single split.

---

## Phase 3: Ensemble (If Classical ML Works)

Only pursue ensemble if at least two classical models (XGBoost, LightGBM, RF) show consistent improvement over baseline.

### 3.1 Voting Ensemble
`python
VotingClassifier(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('rf', rf_model)
    ],
    voting='soft',  # Use probabilities
    weights=[0.5, 0.3, 0.2]  # Based on validation performance
)
`

### 3.2 Weighted Average (Probabilities)
`python
# Simple weighted average of calibrated probabilities
p_ensemble = w1 * p_xgb + w2 * p_lgb + w3 * p_rf
# Weights from validation log-loss (inverse)
weights = 1 / val_logloss
weights = weights / weights.sum()
`

### 3.3 Stacking (Meta-Model)
`python
# Level 0: Base models (XGBoost, LightGBM, RF)
# Level 1: Meta-learner (Logistic Regression on predictions)
StackingClassifier(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('rf', rf_model)
    ],
    final_estimator=LogisticRegression(C=0.1),
    cv=TimeSeriesSplit(n_splits=3, gap=30),  # Temporal CV only!
    stack_method='predict_proba',
    passthrough=False  # Don't pass original features
)
`

### 3.4 Ensemble Weight Determination (NO LEAKAGE)
`python
# CORRECT: Weights from VALIDATION set only
val_preds = {}
for name, model in models.items():
    val_preds[name] = model.predict_proba(X_val)

# Optimize weights on validation set
from scipy.optimize import minimize
def neg_logloss(w):
    w = np.abs(w) / np.abs(w).sum()
    p_ens = sum(w[i] * val_preds[name] for i, name in enumerate(models))
    return log_loss(y_val, p_ens)

result = minimize(neg_logloss, x0=[1/3, 1/3, 1/3])
optimal_weights = np.abs(result.x) / np.abs(result.x).sum()

# Apply to TEST set (never seen during weight optimization)
test_preds = {}
for name, model in models.items():
    test_preds[name] = model.predict_proba(X_test)
p_test_ens = sum(optimal_weights[i] * test_preds[name] for i, name in enumerate(models))
`

NEVER optimize ensemble weights on test set.

### Ensemble Acceptance Criteria
- Must beat best single model on walk-forward test
- Improvement must be statistically significant (bootstrap CI)
- Calibration must not degrade

---

## Phase 4: Deep Learning (Only If Justified)

DO NOT START HERE. Only proceed if:
1. Classical ML + Ensemble shows consistent edge on walk-forward
2. Sufficient data (>1M samples) and compute (GPU)
3. Clear hypothesis for why DL helps (temporal patterns, sequence modeling)

### 4.1 LSTM/GRU
`python
class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, num_layers=2, dropout=0.3, num_classes=3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, 
                           batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, num_classes)
    
    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])  # Last timestep
        return self.fc(out)

# Sequence length: 20-60 days
# Input: Feature sequence per symbol
`
Advantages: Models temporal dependencies, sequence patterns
Disadvantages: Needs sequences (not i.i.d.), much more data, harder to regularize, black box
Overfitting Risk: VERY HIGH

### 4.2 Temporal CNN (TCN)
`python
class TCNModel(nn.Module):
    def __init__(self, input_dim, num_channels=[64, 64, 64], kernel_size=3, dropout=0.2):
        # Dilated causal convolutions
        pass
`
Advantages: Parallel training, long memory, stable gradients
Disadvantages: Still needs sequences, hyperparameter sensitive

### 4.3 Transformer
`python
class TransformerModel(nn.Module):
    def __init__(self, input_dim, d_model=128, nhead=8, num_layers=4, dropout=0.1):
        # Encoder-only transformer with positional encoding
        pass
`
Advantages: Attention mechanism, parallel, long-range dependencies
Disadvantages: Quadratic attention, massive overfitting risk on small data, needs massive regularization

### Deep Learning Acceptance Criteria (Strict)
| Requirement | Threshold |
|-------------|-----------|
| Beats best ensemble on walk-forward | Required |
| Calibration (ECE) | < 0.03 |
| Training stability | No divergence across 5 seeds |
| Inference latency | < 100ms per 1000 symbols |
| Feature importance interpretability | SHAP values stable |

If ANY criterion fails -> Reject DL model. Stay with ensemble.

---

## Hyperparameter Optimization

### Search Space (XGBoost Example)
`python
param_space = {
    'max_depth': [4, 5, 6, 7, 8],
    'learning_rate': [0.01, 0.02, 0.03, 0.05, 0.1],
    'n_estimators': [300, 500, 800],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'min_child_weight': [5, 10, 20],
    'reg_alpha': [0, 0.1, 0.5, 1.0],
    'reg_lambda': [0.5, 1.0, 2.0],
}
`

### Optimization Protocol
1. Optuna with TPE sampler
2. Temporal CV only: TimeSeriesSplit(n_splits=3, gap=30)
3. Objective: Validation log-loss (not accuracy!)
4. Pruning: Median pruner (stop unpromising trials early)
5. Trials: 100-200 per model
6. Seeds: 3 seeds per trial, average metric

### HPO Leakage Prevention
- HPO uses validation set only (within each walk-forward fold)
- Test set never used for HPO
- Best params from each fold -> retrain on train+val -> evaluate on test

---

## Regularization Strategy

### For All Models
1. Early Stopping: Monitor validation loss, patience=50
2. Feature Subsampling: colsample_bytree < 1.0
3. Row Subsampling: subsample < 1.0
4. L2 Regularization: reg_lambda > 0
5. L1 Regularization: reg_alpha > 0 (feature selection)
6. Min Child Weight: Prevent leaf overfitting
7. Max Depth: Limit tree complexity

### For Deep Learning
1. Dropout: 0.2-0.5 on all layers
2. Weight Decay: 1e-4 to 1e-3
3. Gradient Clipping: max_norm=1.0
4. Label Smoothing: 0.1 for classification
5. Mixup/CutMix: Data augmentation (if applicable)

---

## Class Imbalance Handling

Expected class distribution (H5, 2% threshold):
- UP: ~28%
- SIDEWAYS: ~38%
- DOWN: ~34%

### Strategies (Test All)
1. Class Weights: class_weight='balanced' or computed weights
2. Scale Pos Weight (XGBoost): Per-class weight
3. Focal Loss: For neural networks
4. NO SMOTE/Overampling - creates synthetic future data (LEAKAGE!)
5. Threshold Tuning: Optimize decision threshold on validation

---

## Model Comparison Protocol

For each walk-forward fold:
1. Train all models on same training data
2. Evaluate on same validation data (for HPO/early stopping)
3. Final evaluation on same test data
4. Aggregate metrics across folds with bootstrap CI
5. Statistical test: Paired bootstrap test (1000 resamples)

`python
def compare_models(model_a_preds, model_b_preds, y_true, metric_fn, n_bootstrap=1000):
    Paired bootstrap test for model comparison.
    diffs = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        m_a = metric_fn(y_true[idx], model_a_preds[idx])
        m_b = metric_fn(y_true[idx], model_b_preds[idx])
        diffs.append(m_a - m_b)
    
    ci_lower = np.percentile(diffs, 2.5)
    ci_upper = np.percentile(diffs, 97.5)
    p_value = (np.array(diffs) <= 0).mean()  # One-sided: A better than B?
    
    return {
        'mean_diff': np.mean(diffs),
        'ci_95': (ci_lower, ci_upper),
        'p_value': p_value,
        'significant': ci_lower > 0  # A significantly better
    }
`

---

## Computational Requirements

| Model | Train Time (500k samples) | Inference (1000 symbols) | GPU Needed |
|-------|---------------------------|--------------------------|------------|
| Logistic Regression | ~5 sec | ~10 ms | No |
| Random Forest (500) | ~30 sec | ~500 ms | No |
| XGBoost (500) | ~60 sec | ~100 ms | No |
| LightGBM (500) | ~30 sec | ~80 ms | No |
| LSTM | ~10 min | ~500 ms | Yes |
| Transformer | ~30 min | ~1 s | Yes |

v1 Budget: CPU-only, < 5 min total training per walk-forward fold

---

## Summary: Decision Gates

| Gate | Requirement | If Fail |
|------|-------------|---------|
| Baseline | Logistic Regression beats Random on walk-forward | Improve features/labels |
| Classical ML | XGBoost/LightGBM beats Logistic Regression | Stay with Logistic Regression |
| Ensemble | Beats best single model significantly | Use best single model |
| Deep Learning | Beats ensemble on ALL criteria | Reject DL, use ensemble |

Default Path: Logistic Regression -> XGBoost -> LightGBM -> Ensemble (Weighted Avg) -> STOP

Deep Learning is a research exploration, not production path for v1.