import os
path = r'C:\\Programs\\PREDIXA AI\\docs\\12_WALKFORWARD_VALIDATION.md'
content = '''# 12_WALKFORWARD_VALIDATION.md

## Walk-Forward Validation Architecture

This document designs a proper time-series validation framework for financial ML.

## Why Not Random Train/Test Split?

`mermaid
flowchart TD
    A[Random Split] --> B[Shuffles time order]
    B --> C[Future data leaks into training]
    C --> D[Overoptimistic results]
    D --> E[Production failure]
    
    F[Walk-Forward] --> G[Respects temporal order]
    G --> H[Train on past, test on future]
    H --> I[Realistic performance estimate]
    I --> J[Production reliability]
`

Random splitting on time series is fundamentally wrong because:
1. Adjacent days are highly correlated (autocorrelation)
2. Future information leaks into training via nearby samples
3. Model learns temporal patterns that do not generalize

---

## Walk-Forward Validation Design

### Expanding Window (Primary for v1)

Training set grows over time, validation/test fixed ahead.

`mermaid
flowchart LR
    subgraph Fold1 [Fold 1]
        TR1[Train: 2015-2018] --> VA1[Val: 2019] --> TE1[Test: 2020]
    end
    
    subgraph Fold2 [Fold 2]
        TR2[Train: 2015-2019] --> VA2[Val: 2020] --> TE2[Test: 2021]
    end
    
    subgraph Fold3 [Fold 3]
        TR3[Train: 2015-2020] --> VA3[Val: 2021] --> TE3[Test: 2022]
    end
    
    subgraph Fold4 [Fold 4]
        TR4[Train: 2015-2021] --> VA4[Val: 2022] --> TE4[Test: 2023]
    end
    
    subgraph Fold5 [Fold 5]
        TR5[Train: 2015-2022] --> VA5[Val: 2023] --> TE5[Test: 2024]
    end
`

### Rolling Window (Alternative)

Fixed training window size, slides forward.

`mermaid
flowchart LR
    subgraph Fold1 [Fold 1]
        TR1[Train: 2015-2018] --> VA1[Val: 2019] --> TE1[Test: 2020]
    end
    
    subgraph Fold2 [Fold 2]
        TR2[Train: 2016-2019] --> VA2[Val: 2020] --> TE2[Test: 2021]
    end
    
    subgraph Fold3 [Fold 3]
        TR3[Train: 2017-2020] --> VA3[Val: 2021] --> TE3[Test: 2022]
    end
`

### Comparison

| Aspect | Expanding Window | Rolling Window |
|--------|------------------|----------------|
| Data Usage | Increases over time | Fixed |
| Model Stability | Improves with more data | Constant |
| Regime Adaptation | Slower | Faster |
| Compute Cost | Increases | Constant |
| v1 Choice | Primary | Secondary |

---

## Purged/Embargoed Cross-Validation

Critical for preventing leakage between train/validation/test.

`mermaid
flowchart LR
    subgraph Standard [Standard K-Fold - WRONG]
        S1[Train] --> S2[Val]
        S2 --> S3[Test]
    end
    
    subgraph Purged [Purged/Embargoed - CORRECT]
        P1[Train] --> P2[Embargo Gap]
        P2 --> P3[Validation]
        P3 --> P4[Embargo Gap]
        P4 --> P5[Test]
    end
`

### Implementation

`python
from sklearn.model_selection import TimeSeriesSplit

def purged_time_series_split(n_splits=5, test_size=None, gap=30, embargo_pct=0.01):
    # TimeSeriesSplit with purge and embargo.
    # Args:
    #     n_splits: Number of folds
    #     test_size: Size of test set (if None, equal splits)
    #     gap: Days between train and validation (purge)
    #     embargo_pct: % of test set to embargo after validation
    # Returns:
    #     Generator of (train_idx, val_idx, test_idx)
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=gap)
    
    for train_idx, test_idx in tscv.split(X):
        # Further split test into val + test with embargo
        n_test = len(test_idx)
        n_embargo = int(n_test * embargo_pct)
        n_val = n_test - n_embargo
        
        val_idx = test_idx[:n_val]
        test_idx_final = test_idx[n_val + n_embargo:]
        
        yield train_idx, val_idx, test_idx_final
`

### Why Embargo?
- Adjacent days have correlated returns
- Without embargo, validation samples are too similar to test
- Embargo of 1-5% of test period (e.g., 5-30 days) breaks correlation

---

## Walk-Forward Validation Protocol

### Complete Protocol

`python
class WalkForwardValidator:
    def __init__(self, config):
        self.config = config
        self.results = []
    
    def validate(self, X, y, model_factory, feature_pipeline):
        # Run complete walk-forward validation.
        # Steps per fold:
        # 1. Split data temporally
        # 2. Fit feature pipeline on train only
        # 3. Train model on train
        # 4. Tune hyperparameters on validation
        # 5. Calibrate on calibration set (from validation)
        # 6. Evaluate on test
        # 7. Store all artifacts
        splits = self._generate_splits(X.index.get_level_values('date').unique())
        
        for fold_idx, (train_dates, val_dates, test_dates) in enumerate(splits):
            print(f'=== Fold {fold_idx}: Train={train_dates[0]}-{train_dates[-1]}, Val={val_dates[0]}-{val_dates[-1]}, Test={test_dates[0]}-{test_dates[-1]} ===')
            
            # 1. Split data
            X_train, y_train = self._get_data(X, y, train_dates)
            X_val, y_val = self._get_data(X, y, val_dates)
            X_test, y_test = self._get_data(X, y, test_dates)
            
            # 2. Feature pipeline (fit on train only!)
            feature_pipeline.fit(X_train, y_train)
            X_train_feat = feature_pipeline.transform(X_train)
            X_val_feat = feature_pipeline.transform(X_val)
            X_test_feat = feature_pipeline.transform(X_test)
            
            # 3. Train base model
            model = model_factory()
            model.fit(X_train_feat, y_train)
            
            # 4. Hyperparameter tuning on validation
            best_params = self._tune_hyperparams(model_factory, X_train_feat, y_train, X_val_feat, y_val)
            model = model_factory(**best_params)
            model.fit(X_train_feat, y_train)
            
            # 5. Calibration (use portion of validation as cal set)
            X_cal, y_cal = self._split_calibration(X_val_feat, y_val)
            X_val_final, y_val_final = X_val_feat, y_val
            
            calibrated_model = self._calibrate(model, X_train_feat, y_train, X_val_final, y_val_final, X_cal, y_cal)
            
            # 6. Evaluate on test (NEVER seen before!)
            test_probs = calibrated_model.predict_proba(X_test_feat)
            test_preds = test_probs.argmax(axis=1)
            
            metrics = self._compute_all_metrics(y_test, test_probs, test_preds)
            
            # 7. Store results
            fold_result = {
                'fold': fold_idx,
                'train_period': (train_dates[0], train_dates[-1]),
                'val_period': (val_dates[0], val_dates[-1]),
                'test_period': (test_dates[0], test_dates[-1]),
                'best_params': best_params,
                'metrics': metrics,
                'model': calibrated_model,
                'feature_version': feature_pipeline.version,
            }
            self.results.append(fold_result)
        
        return self._aggregate_results()
    
    def _generate_splits(self, all_dates):
        # Implementation depends on config (expanding/rolling, gaps, etc.)
        pass
`

### Per-Fold Metrics Collection

`python
def compute_fold_metrics(y_true, y_prob, y_pred):
    # Compute comprehensive metrics for one fold.
    return {
        # Classification
        'accuracy': accuracy_score(y_true, y_pred),
        'precision_macro': precision_score(y_true, y_pred, average='macro'),
        'recall_macro': recall_score(y_true, y_pred, average='macro'),
        'f1_macro': f1_score(y_true, y_pred, average='macro'),
        'roc_auc_ovr': roc_auc_score(y_true, y_prob, multi_class='ovr'),
        'roc_auc_ovo': roc_auc_score(y_true, y_prob, multi_class='ovo'),
        'pr_auc_macro': average_precision_score(y_true, y_prob, average='macro'),
        
        # Probabilistic
        'log_loss': log_loss(y_true, y_prob),
        'brier_score': brier_score(y_true, y_prob),
        'ece': expected_calibration_error(y_true, y_prob),
        'mce': maximum_calibration_error(y_true, y_prob),
        
        # Per-class
        'precision_per_class': precision_score(y_true, y_pred, average=None).tolist(),
        'recall_per_class': recall_score(y_true, y_pred, average=None).tolist(),
        'f1_per_class': f1_score(y_true, y_pred, average=None).tolist(),
        
        # Confusion matrix
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
    }
`

---

## Aggregation Across Folds

### Bootstrap Confidence Intervals

`python
def aggregate_walkforward_results(fold_results, n_bootstrap=1000):
    # Aggregate metrics across folds with bootstrap CI.
    metrics_keys = fold_results[0]['metrics'].keys()
    aggregated = {}
    
    for key in metrics_keys:
        values = [r['metrics'][key] for r in fold_results]
        
        # Mean and std across folds
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # Bootstrap CI
        boot_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(values, size=len(values), replace=True)
            boot_means.append(np.mean(sample))
        
        ci_lower = np.percentile(boot_means, 2.5)
        ci_upper = np.percentile(boot_means, 97.5)
        
        aggregated[key] = {
            'mean': mean_val,
            'std': std_val,
            'ci_95': (ci_lower, ci_upper),
            'per_fold': values,
        }
    
    return aggregated
`

### Stability Checks

`python
def check_stability(fold_results):
    # Check metric stability across folds.
    metrics_df = pd.DataFrame([r['metrics'] for r in fold_results])
    
    stability_report = {}
    for col in metrics_df.columns:
        cv = metrics_df[col].std() / metrics_df[col].mean()
        trend = np.polyfit(range(len(metrics_df)), metrics_df[col], 1)[0]
        
        stability_report[col] = {
            'cv': cv,
            'trend_per_fold': trend,
            'min': metrics_df[col].min(),
            'max': metrics_df[col].max(),
            'stable': cv < 0.1 and abs(trend) < 0.01
        }
    
    return stability_report
`

---

## Model Selection in Walk-Forward

### Correct Model Selection

`python
def select_model_walkforward(candidate_models, X, y, feature_pipeline):
    # Select best model using walk-forward validation.
    # CRITICAL: Model selection uses VALIDATION performance.
    # Final evaluation on TEST is for reporting only.
    model_scores = {}
    
    for model_name, model_factory in candidate_models.items():
        validator = WalkForwardValidator(config)
        results = validator.validate(X, y, model_factory, feature_pipeline)
        
        # Use validation log-loss for selection (averaged across folds)
        val_scores = []
        for fold in results['per_fold_details']:
            val_scores.append(fold['val_log_loss'])
        
        model_scores[model_name] = {
            'mean_val_logloss': np.mean(val_scores),
            'std_val_logloss': np.std(val_scores),
            'test_metrics': results['aggregated_test_metrics'],
        }
    
    # Select best by validation performance
    best_model = min(model_scores.items(), key=lambda x: x[1]['mean_val_logloss'])[0]
    
    return best_model, model_scores
`

### Hyperparameter Tuning Per Fold

`python
def tune_hyperparams_per_fold(model_factory, X_train, y_train, X_val, y_val):
    # Tune hyperparameters on validation set within each fold.
    
    def objective(trial):
        params = {
            'max_depth': trial.suggest_int('max_depth', 4, 8),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 200, 800),
            'subsample': trial.suggest_float('subsample', 0.7, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 5, 30),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 2.0),
        }
        
        model = model_factory(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=50, verbose=False)
        
        val_probs = model.predict_proba(X_val)
        return log_loss(y_val, val_probs)
    
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=100)
    
    return study.best_params
`

---

## Retraining Frequency

### When to Retrain

`python
class RetrainingSchedule:
    def __init__(self, config):
        self.config = config
        self.last_train_date = None
    
    def should_retrain(self, current_date, performance_metrics):
        # Determine if retraining is needed.
        
        # Scheduled retraining
        if self.config.schedule == 'monthly':
            if self.last_train_date is None:
                return True
            if (current_date - self.last_train_date).days >= 30:
                return True
        
        elif self.config.schedule == 'quarterly':
            if self.last_train_date is None:
                return True
            if (current_date - self.last_train_date).days >= 90:
                return True
        
        # Trigger-based: performance degradation
        if self.config.trigger_enabled:
            recent_perf = performance_metrics.get('recent_logloss')
            baseline_perf = performance_metrics.get('baseline_logloss')
            
            if recent_perf and baseline_perf:
                degradation = (recent_perf - baseline_perf) / baseline_perf
                if degradation > self.config.degradation_threshold:
                    return True
        
        # Trigger-based: drift detection
        if self.config.drift_enabled:
            drift_score = performance_metrics.get('drift_score')
            if drift_score and drift_score > self.config.drift_threshold:
                return True
        
        return False
`

---

## Validation Data Requirements

### Minimum Data for Walk-Forward

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Training (initial) | 3 years (750 days) | 5+ years |
| Validation per fold | 6 months (126 days) | 1 year |
| Test per fold | 6 months (126 days) | 1 year |
| Embargo gap | 30 days | 30-60 days |
| Number of folds | 3 | 5+ |
| Total history | 4.5 years | 7+ years |

### Data Sufficiency Check

`python
def check_data_sufficiency(data_start, data_end, config):
    # Verify enough data for walk-forward validation.
    total_days = (data_end - data_start).days
    trading_days = total_days * 5 / 7
    
    min_required = (config.min_train_years * 252 + config.n_folds * (config.val_months + config.test_months) * 21 + config.n_folds * config.embargo_days)
    
    return {
        'available_days': trading_days,
        'required_days': min_required,
        'sufficient': trading_days >= min_required,
        'max_folds': int((trading_days - config.min_train_years * 252) / ((config.val_months + config.test_months) * 21 + config.embargo_days))
    }
`

---

## Common Walk-Forward Mistakes

| Mistake | Why Wrong | Fix |
|---------|-----------|-----|
| No embargo gap | Validation leaks into test | Add 30-day embargo |
| Feature fitting on all data | Leakage | Fit features on train only |
| Hyperparameter tuning on test | Selection bias | Tune on validation only |
| Single fold | No confidence intervals | Minimum 3 folds |
| Fixed train size (rolling) without justification | Wastes data | Use expanding for v1 |
| Ignoring regime changes | Model may not adapt | Track regime-conditional metrics |
| No bootstrap CI | No uncertainty quantification | Always report CI |

---

## Reporting Standard

Every walk-forward validation report must include:

`markdown
## Walk-Forward Validation Report

### Configuration
- Split method: Expanding / Rolling
- Initial training period: YYYY-MM-DD to YYYY-MM-DD
- Validation period per fold: N months
- Test period per fold: N months
- Embargo gap: N days
- Number of folds: N

### Per-Fold Results
| Fold | Train Period | Val Period | Test Period | Val LogLoss | Test LogLoss | Test AUC | Test ECE |
|------|--------------|------------|-------------|-------------|--------------|----------|----------|
| 1 | ... | ... | ... | ... | ... | ... | ... |

### Aggregated Results (with 95% CI)
| Metric | Mean | Std | CI Lower | CI Upper | Stable? |
|--------|------|-----|----------|----------|---------|
| Log Loss | ... | ... | ... | ... | Yes/No |
| ROC-AUC | ... | ... | ... | ... | Yes/No |
| ECE | ... | ... | ... | ... | Yes/No |

### Stability Analysis
- Metric CV across folds: [values]
- Trend detected: [Yes/No, which metrics]
- Regime-conditional performance: [table]

### Model Selection
- Selected model: [name]
- Selection criterion: Validation log-loss
- Candidates compared: [list with scores]

### Conclusion
- Model passes validation: [Yes/No]
- Key concerns: [list]
- Recommended next steps: [list]
`

---

## Summary

| Aspect | Decision |
|--------|----------|
| Primary Method | Expanding Window |
| Alternative | Rolling Window (v2) |
| CV Type | Purged/Embargoed TimeSeriesSplit |
| Embargo Gap | 30 days |
| Min Folds | 5 |
| Model Selection | Validation log-loss |
| HPO | Per-fold on validation |
| Calibration | Separate cal set from validation |
| Aggregation | Bootstrap CI (1000 samples) |
| Stability Check | CV < 10%, no trend |

Golden Rule: If it works in walk-forward with embargo, it might work in production. If it only works in random split, it will fail.'''
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('12_WALKFORWARD_VALIDATION.md created')

