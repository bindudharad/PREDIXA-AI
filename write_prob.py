import os
path = r'C:\Programs\PREDIXA AI\docs\10_PROBABILITY_CONFIDENCE.md'
content = '''# 10_PROBABILITY_CONFIDENCE.md

## Probability and Confidence System

This document designs the probability calibration, confidence scoring, and uncertainty quantification for predictions.

## Core Distinction: Probability vs Confidence

| Concept | Definition | Range | Interpretation |
|---------|------------|-------|----------------|
| Probability | Calibrated P(class | features) | [0, 1] | Frequency interpretation: if P(UP)=0.7, then ~70% of such predictions should be UP |
| Confidence | Model certainty in its prediction | [0, 1] | Epistemic uncertainty: how much we trust this specific prediction |

Critical: A model can be confident (low entropy) but wrong. A model can be uncertain (high entropy) but correct. They measure different things.

---

## Probability Calibration

### Why Calibration Matters

Raw model outputs (logits, tree votes) are NOT probabilities. They need calibration.

`mermaid
flowchart LR
    A[Raw Model Output Logits / Votes] --> B[Calibration Platt / Isotonic]
    B --> C[Calibrated Probabilities P(UP), P(DOWN), P(SIDEWAYS)]
    C --> D[Reliability Diagram ECE, MCE, Brier]
    D --> E{Good Calibration?}
    E -->|No| B
    E -->|Yes| F[Production Use]
`

### Calibration Methods

#### 1. Platt Scaling (Sigmoid)

`python
from sklearn.calibration import CalibratedClassifierCV

# For models with predict_proba (logistic regression, neural nets)
calibrated = CalibratedClassifierCV(base_model, method='sigmoid', cv=3)
calibrated.fit(X_train, y_train)

# Best for: Models with reasonably calibrated outputs already
# Limitation: Assumes sigmoid shape, cannot fix severe miscalibration
`

#### 2. Isotonic Regression (Primary Choice)

`python
# Non-parametric, flexible, handles any miscalibration shape
calibrated = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
calibrated.fit(X_train, y_train)

# Best for: Tree models (XGBoost, RF), complex miscalibration
# Requirement: More data (min ~1000 samples per class)
# Risk: Can overfit on small calibration sets
`

#### 3. Temperature Scaling (For Neural Networks)

`python
# Single parameter T > 0 applied to logits before softmax
# T = 1: no change; T > 1: softer; T < 1: sharper
class TemperatureScaling:
    def __init__(self):
        self.temperature = 1.0
    
    def fit(self, logits, labels):
        from scipy.optimize import minimize
        def nll(T):
            probs = softmax(logits / T, axis=1)
            return log_loss(labels, probs)
        result = minimize(nll, x0=1.0, bounds=[(0.01, 10)])
        self.temperature = result.x[0]
    
    def predict_proba(self, logits):
        return softmax(logits / self.temperature, axis=1)
`

### Calibration Protocol (NO LEAKAGE)

`python
def calibrate_model(model, X_train, y_train, X_val, y_val, X_cal, y_cal):
    # Three-way split for calibration:
    # Train: Model training
    # Val: Hyperparameter tuning, early stopping
    # Cal: Calibration fitting (held out from both!)
    # 1. Train model on train
    model.fit(X_train, y_train)
    
    # 2. Tune/early stop on val (already done)
    
    # 3. Calibrate on SEPARATE calibration set
    calibrated = CalibratedClassifierCV(model, method='isotonic', cv='prefit')
    calibrated.fit(X_cal, y_cal)
    
    # 4. Evaluate on test (never seen!)
    return calibrated
`

Data Split for Calibration:
- Train: 60%
- Validation: 20% (for HPO, early stopping)
- Calibration: 10% (for Platt/Isotonic fitting)
- Test: 10% (final evaluation)

In walk-forward: Each fold gets its own calibration set from the validation period.

---

## Calibration Evaluation Metrics

### 1. Reliability Diagram
`python
def reliability_diagram(y_true, y_prob, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob.max(axis=1), bin_edges) - 1
    
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []
    
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_confidences.append(y_prob[mask].max(axis=1).mean())
            bin_accuracies.append((y_true[mask] == y_prob[mask].argmax(axis=1)).mean())
            bin_counts.append(mask.sum())
        else:
            bin_confidences.append((bin_edges[i] + bin_edges[i+1]) / 2)
            bin_accuracies.append((bin_edges[i] + bin_edges[i+1]) / 2)
            bin_counts.append(0)
    
    return bin_edges[:-1], np.array(bin_accuracies), np.array(bin_confidences), np.array(bin_counts)
`

### 2. Expected Calibration Error (ECE)
`python
def expected_calibration_error(y_true, y_prob, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob.max(axis=1), bin_edges) - 1
    
    ece = 0.0
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_conf = y_prob[mask].max(axis=1).mean()
            bin_acc = (y_true[mask] == y_prob[mask].argmax(axis=1)).mean()
            bin_weight = mask.sum() / len(y_true)
            ece += bin_weight * abs(bin_acc - bin_conf)
    
    return ece
`

### 3. Maximum Calibration Error (MCE)
`python
def maximum_calibration_error(y_true, y_prob, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob.max(axis=1), bin_edges) - 1
    
    mce = 0.0
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_conf = y_prob[mask].max(axis=1).mean()
            bin_acc = (y_true[mask] == y_prob[mask].argmax(axis=1)).mean()
            mce = max(mce, abs(bin_acc - bin_conf))
    
    return mce
`

### 4. Brier Score (Proper Scoring Rule)
`python
def brier_score(y_true, y_prob):
    n_classes = y_prob.shape[1]
    y_onehot = np.eye(n_classes)[y_true]
    return np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1))
`

### 5. Log Loss (Cross-Entropy)
`python
from sklearn.metrics import log_loss

# Primary metric for probability quality
# Lower = better calibrated AND more confident correct predictions
logloss = log_loss(y_true, y_prob)
`

### Calibration Targets (v1)

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| ECE | < 0.02 | < 0.05 |
| MCE | < 0.05 | < 0.10 |
| Brier Score | < 0.25 | < 0.35 |
| Log Loss | < 0.90 | < 1.10 |
| Reliability Diagram | Near diagonal | Visual check |

---

## Confidence Scoring

### Confidence Not Equal Max Probability

`python
def compute_confidence(probabilities, method='entropy'):
    if method == 'entropy':
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
        max_entropy = np.log(probabilities.shape[1])
        confidence = 1 - entropy / max_entropy
    
    elif method == 'margin':
        sorted_probs = np.sort(probabilities, axis=1)
        confidence = sorted_probs[:, -1] - sorted_probs[:, -2]
    
    elif method == 'max_prob':
        confidence = probabilities.max(axis=1)
    
    elif method == 'gini':
        gini = 1 - np.sum(probabilities ** 2, axis=1)
        max_gini = 1 - 1/probabilities.shape[1]
        confidence = 1 - gini / max_gini
    
    return confidence
`

### Recommended: Entropy-Based Confidence

`python
confidence = compute_confidence(probs, method='entropy')

# Interpretation:
# confidence > 0.8: High confidence (low entropy)
# confidence 0.5-0.8: Medium confidence
# confidence < 0.5: Low confidence (high entropy) -> consider no-trade
`

### Confidence Calibration

Confidence should also be calibrated! High confidence predictions should be more accurate.

`python
def confidence_calibration_curve(y_true, y_prob, confidence, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(confidence, bin_edges) - 1
    
    results = []
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            acc = (y_true[mask] == y_prob[mask].argmax(axis=1)).mean()
            avg_conf = confidence[mask].mean()
            results.append({'bin': i, 'accuracy': acc, 'confidence': avg_conf, 'count': mask.sum()})
    
    return pd.DataFrame(results)
`

---

## Prediction Output Format

`python
@dataclass
class Prediction:
    symbol: str
    prediction_timestamp: pd.Timestamp
    model_version: str
    feature_version: str
    horizon_days: int
    
    # Probabilities (calibrated, sum to 1)
    p_up: float
    p_down: float
    p_sideways: float
    
    # Confidence (entropy-based)
    confidence: float
    
    # Expected return (probability-weighted)
    expected_return: float
    
    # Top features (for explainability)
    top_features: List[Tuple[str, float]]
    
    # Metadata
    feature_hash: str
    
    def to_dict(self):
        return asdict(self)
`

### Example Output
`json
{
  
symbol: AAPL,
  prediction_timestamp: 2024-01-15T21:00:00Z,
  model_version: model_xgboost_v1.2.0,
  feature_version: feat_v1.3,
  horizon_days: 5,
  p_up: 0.68,
  p_down: 0.11,
  p_sideways: 0.21,
  confidence: 0.76,
  expected_return: 0.018,
  top_features: [
    [momentum_20d, 0.15],
    [rel_str_20d, 0.12],
    [rsi_14, -0.08],
    [vol_20d, -0.06]
  ],
  feature_hash: a1b2c3d4e5f6
}
`

---

## No-Trade Conditions Based on Confidence

`python
def should_trade(prediction, config):
    if prediction.confidence < config.get('min_confidence', 0.55):
        return False, fConfidence
prediction.confidence:.2f
below
threshold
config['min_confidence']

    
    max_prob = max(prediction.p_up, prediction.p_down, prediction.p_sideways)
    if max_prob < config.get('min_max_prob', 0.40):
        return False, f
Max
probability
max_prob:.2f
below
threshold
config['min_max_prob']

    
    if prediction.p_up > 0.35 and prediction.p_down > 0.35:
        return False, 
Conflicting
UP/DOWN
signals
    
    return True, OK
`

---

## Uncertainty Quantification

Beyond point probabilities, quantify prediction uncertainty.

### 1. Prediction Intervals (Conformal Prediction)
`python
def conformal_prediction_set(calibrated_model, X_cal, y_cal, X_test, alpha=0.1):
    cal_probs = calibrated_model.predict_proba(X_cal)
    cal_scores = 1 - cal_probs[np.arange(len(y_cal)), y_cal]
    
    q_hat = np.quantile(cal_scores, np.ceil((len(cal_scores)+1)*(1-alpha)) / len(cal_scores))
    
    test_probs = calibrated_model.predict_proba(X_test)
    prediction_sets = []
    for probs in test_probs:
        pred_set = [c for c in range(3) if (1 - probs[c]) <= q_hat]
        prediction_sets.append(pred_set if pred_set else [probs.argmax()])
    
    return prediction_sets, test_probs
`

### 2. Model Uncertainty (Ensemble Variance)
`python
def ensemble_uncertainty(base_models, X):
    all_probs = np.stack([m.predict_proba(X) for m in base_models.values()], axis=0)
    mean_probs = all_probs.mean(axis=0)
    var_probs = all_probs.var(axis=0)
    
    total_uncertainty = var_probs.sum(axis=1)
    mean_entropy = -np.sum(mean_probs * np.log(mean_probs + 1e-10), axis=1)
    expected_entropy = np.mean(-np.sum(all_probs * np.log(all_probs + 1e-10), axis=2), axis=0)
    epistemic = mean_entropy - expected_entropy
    aleatoric = expected_entropy
    
    return {
        'total_uncertainty': total_uncertainty,
        'epistemic': epistemic,
        'aleatoric': aleatoric,
        'mean_probs': mean_probs
    }
`

### 3. Feature-Level Uncertainty
`python
def feature_uncertainty(shap_values_list):
    shap_array = np.stack(shap_values_list, axis=0)
    mean_shap = shap_array.mean(axis=0)
    std_shap = shap_array.std(axis=0)
    return mean_shap, std_shap
`

---

## Summary: Probability Pipeline

`mermaid
flowchart TD
    A[Raw Model Outputs Logits / Tree Votes] --> B[Individual Model Calibration Isotonic/Platt]
    B --> C[Calibrated Probabilities Per Model]
    C --> D[Ensemble Weighted Average]
    D --> E[Ensemble Calibration Isotonic on Cal Set]
    E --> F[Final Probabilities P(UP), P(DOWN), P(SIDEWAYS)]
    F --> G[Confidence Score Entropy-based]
    F --> H[Expected Return Sum p_i * r_i]
    F --> I[Prediction Interval Conformal]
    F --> J[Uncertainty Ensemble Variance]
`

---

## Key Rules

1. Calibrate after ensemble, not before
2. Use held-out calibration set (not validation, not test)
3. Evaluate calibration on test set only
4. Report ECE, MCE, Brier, Log Loss for every model version
5. Confidence is separate from probability - both reported
6. No-trade on low confidence - configurable threshold
7. Track calibration drift in production monitoring

---

## Calibration Monitoring in Production

`python
def monitor_calibration(production_predictions, outcomes, window_days=30):
    recent = production_predictions[production_predictions.timestamp > production_predictions.timestamp.max() - pd.Timedelta(days=window_days)]
    
    merged = recent.merge(outcomes, on=['symbol', 'prediction_date'])
    
    y_true = merged['actual_label'].values
    y_prob = merged[['p_up', 'p_down', 'p_sideways']].values
    
    ece = expected_calibration_error(y_true, y_prob)
    mce = maximum_calibration_error(y_true, y_prob)
    brier = brier_score(y_true, y_prob)
    logloss = log_loss(y_true, y_prob)
    
    return {
        'window_days': window_days,
        'n_predictions': len(merged),
        'ece': ece,
        'mce': mce,
        'brier': brier,
        'log_loss': logloss,
        'alert': ece > 0.05 or mce > 0.10
    }
`

Alert if ECE > 0.05 or MCE > 0.10 on 30-day rolling'''
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('10_PROBABILITY_CONFIDENCE.md created')

