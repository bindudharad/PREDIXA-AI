# 17_MODEL_MONITORING.md

## Model Monitoring Design

This document designs production monitoring for the PREDIXA AI system.

## Monitoring Overview

`mermaid
flowchart TD
    subgraph Inputs [Monitoring Inputs]
        I1[Live Predictions]
        I2[Actual Outcomes]
        I3[Feature Data]
        I4[Model Artifacts]
    end
    
    subgraph Detectors [Drift Detectors]
        D1[Prediction Drift]
        D2[Feature Drift]
        D3[Performance Drift]
        D4[Data Quality]
    end
    
    subgraph Actions [Actions]
        A1[Alert]
        A2[Investigate]
        A3[Retrain Trigger]
        A4[Rollback]
    end
    
    I1 --> D1
    I2 --> D3
    I3 --> D2
    I4 --> D3
    D1 --> A1
    D2 --> A1
    D3 --> A1
    D4 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
`

## What to Monitor

### 1. Prediction Distribution Drift
- Track distribution of predicted probabilities over time
- Compare to training/validation distribution
- Metrics: Population Stability Index (PSI), KS test, Wasserstein distance

### 2. Feature Distribution Drift
- Track distribution of each input feature
- Detect shifts in feature statistics
- Metrics: PSI per feature, mean/std shift, missing rate

### 3. Performance Drift
- Track model metrics on resolved predictions
- Compare to expected performance from validation
- Metrics: Log loss, accuracy, ECE, Brier score

### 4. Calibration Drift
- Reliability diagram over rolling windows
- ECE and MCE tracking
- Detect miscalibration early

### 5. Data Quality
- Missing data rates
- Feature freshness
- Anomaly detection in input features

### 6. Operational Metrics
- Prediction latency
- API error rates
- Throughput

## Drift Detection Methods

### Population Stability Index (PSI)
`python
def psi(expected, actual, bins=10):
    Expected and actual are arrays of predictions/feature values.
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins+1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    
    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    
    expected_pct = np.clip(expected_pct, 0.0001, None)
    actual_pct = np.clip(actual_pct, 0.0001, None)
    
    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return psi_val

# Thresholds:
# PSI < 0.1: No significant drift
# 0.1 <= PSI < 0.25: Moderate drift
# PSI >= 0.25: Significant drift
`

### Kolmogorov-Smirnov Test
`python
from scipy.stats import ks_2samp

def ks_drift(reference, current):
    KS test for distribution drift.
    statistic, p_value = ks_2samp(reference, current)
    return {'statistic': statistic, 'p_value': p_value, 'drift': p_value < 0.05}
`

### ADWIN (Adaptive Windowing)
`python
# For streaming drift detection
# Detects concept drift in online setting
from river.drift import ADWIN

adwin = ADWIN()
for pred_prob in prediction_stream:
    adwin.update(pred_prob)
    if adwin.drift_detected:
        alert('Drift detected in prediction stream')
`

### Performance Monitoring
`python
def monitor_performance(predictions, outcomes, window_days=30):
    recent = predictions[predictions.timestamp > predictions.timestamp.max() - pd.Timedelta(days=window_days)]
    merged = recent.merge(outcomes, on=['symbol', 'prediction_date'])
    
    if len(merged) < 100:
        return {'status': 'insufficient_data'}
    
    y_true = merged['actual_class'].values
    y_prob = merged[['p_up', 'p_down', 'p_sideways']].values
    y_pred = merged['predicted_class'].values
    
    return {
        'window_days': window_days,
        'n_samples': len(merged),
        'log_loss': log_loss(y_true, y_prob),
        'accuracy': accuracy_score(y_true, y_pred),
        'ece': expected_calibration_error(y_true, y_prob),
        'brier': brier_score(y_true, y_prob),
        'roc_auc': roc_auc_score(y_true, y_prob, multi_class='ovr'),
    }
`

## Alerting Rules

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|-------------------|--------|
| PSI (predictions) | 0.1 | 0.25 | Alert + Investigate |
| PSI (features) | 0.1 | 0.2 | Alert + Investigate |
| Log Loss increase | >10% | >25% | Alert + Retrain trigger |
| ECE | 0.05 | 0.10 | Recalibrate |
| Accuracy drop | >5% | >10% | Investigate |
| Data freshness | >2hrs | >6hrs | Alert |
| Prediction latency | >500ms | >2s | Alert |
| API error rate | >1% | >5% | Alert |

## Monitoring Dashboard

Key panels:
1. **Prediction Distribution**: Histogram of P(UP), P(DOWN), P(SIDEWAYS) over time
2. **Feature Drift**: PSI per feature over time (heatmap)
3. **Performance**: Rolling log loss, accuracy, ECE
4. **Calibration**: Reliability diagram (current vs reference)
5. **Data Quality**: Missing rates, freshness
6. **Operational**: Latency, throughput, errors

## Automated Retraining Trigger

`python
class RetrainingTrigger:
    def __init__(self, config):
        self.config = config
    
    def check(self, monitoring_results):
        triggers = []
        
        # Performance degradation
        if monitoring_results.get('log_loss_increase', 0) > self.config.perf_threshold:
            triggers.append('performance_degradation')
        
        # Feature drift
        max_feature_psi = max(monitoring_results.get('feature_psi', {}).values(), default=0)
        if max_feature_psi > self.config.feature_drift_threshold:
            triggers.append('feature_drift')
        
        # Prediction drift
        if monitoring_results.get('prediction_psi', 0) > self.config.pred_drift_threshold:
            triggers.append('prediction_drift')
        
        # Calibration drift
        if monitoring_results.get('ece', 0) > self.config.calibration_threshold:
            triggers.append('calibration_drift')
        
        return triggers
`

## Human-in-the-Loop

All retraining triggers require human approval:
1. Alert sent to Slack/email
2. Data scientist investigates
3. If confirmed, candidate model trained
4. Candidate validated on recent holdout
5. If better, shadow deployment
6. If shadow successful, promote

Never automatic promotion without validation.

## Summary

| Component | Method | Frequency |
|-----------|--------|-----------|
| Prediction Drift | PSI, KS test | Daily |
| Feature Drift | PSI per feature | Daily |
| Performance Drift | Rolling metrics | Daily |
| Calibration Drift | ECE, reliability diagram | Daily |
| Data Quality | Missing rate, freshness | Hourly |
| Operational | Latency, errors | Real-time |
| Retraining Trigger | Multi-signal | On alert |
