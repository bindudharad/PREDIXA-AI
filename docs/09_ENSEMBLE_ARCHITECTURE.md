# 09_ENSEMBLE_ARCHITECTURE.md

## Ensemble Architecture

This document designs the ensemble system for combining multiple model predictions into a unified probability estimate.

## Ensemble Philosophy

- Diversity over complexity: Combine models with different inductive biases
- No leakage in weight optimization: Weights determined on validation data only
- Calibration preservation: Ensemble must maintain or improve calibration
- Interpretability: Each model contribution traceable

## Component Models

`mermaid
flowchart TD
    subgraph BaseModels [Base Models]
        M1[XGBoost Technical Features]
        M2[LightGBM Technical Features]
        M3[Random Forest Technical Features]
        M4[XGBoost + Fundamental]
        M5[XGBoost + News Sentiment]
        M6[Logistic Regression All Features]
    end
    
    subgraph Specialized [Specialized Models]
        S1[Regime Model Bull/Bear/Sideways]
        S2[Volatility Model High/Low Vol]
        S3[Sector Model Per-Sector]
    end
    
    subgraph Ensemble [Ensemble Layer]
        E1[Weighted Average Probabilities]
        E2[Stacking Meta-Learner]
        E3[Voting Soft Voting]
    end
    
    subgraph Output [Final Output]
        O1[Calibrated Probabilities P(UP), P(DOWN), P(SIDEWAYS)]
        O2[Confidence Score]
        O3[Model Contributions]
    end
    
    M1 --> E1
    M2 --> E1
    M3 --> E1
    M4 --> E1
    M5 --> E1
    M6 --> E1
    S1 --> E2
    S2 --> E2
    S3 --> E2
    E1 --> O1
    E2 --> O1
    E3 --> O1
    O1 --> O2
    O1 --> O3
`

## Ensemble Methods

### Method 1: Weighted Average (Primary for v1)

Simple, interpretable, leakage-proof.

`python
class WeightedAverageEnsemble:
    def __init__(self, models: dict, weight_method='inv_logloss'):
        self.models = models
        self.weight_method = weight_method
        self.weights = None
    
    def fit_weights(self, X_val, y_val):
        val_probs = {}
        for name, model in self.models.items():
            val_probs[name] = model.predict_proba(X_val)
        
        if self.weight_method == 'inv_logloss':
            losses = {name: log_loss(y_val, probs) for name, probs in val_probs.items()}
            inv_losses = {name: 1.0 / loss for name, loss in losses.items()}
            total = sum(inv_losses.values())
            self.weights = {name: w/total for name, w in inv_losses.items()}
        
        elif self.weight_method == 'optimize':
            from scipy.optimize import minimize
            
            def objective(w):
                w = np.abs(w) / np.abs(w).sum()
                p_ens = sum(w[i] * list(val_probs.values())[i] for i in range(len(val_probs)))
                return log_loss(y_val, p_ens)
            
            n = len(val_probs)
            result = minimize(objective, x0=np.ones(n)/n, bounds=[(0, 1)]*n, constraints={'type': 'eq', 'fun': lambda w: w.sum() - 1})
            w_opt = np.abs(result.x) / np.abs(result.x).sum()
            self.weights = dict(zip(val_probs.keys(), w_opt))
        
        elif self.weight_method == 'uniform':
            n = len(self.models)
            self.weights = {name: 1.0/n for name in self.models}
        
        return self.weights
    
    def predict_proba(self, X):
        if self.weights is None:
            raise ValueError('Call fit_weights first')
        
        probs = np.zeros((X.shape[0], 3))
        for name, model in self.models.items():
            probs += self.weights[name] * model.predict_proba(X)
        
        return probs
    
    def get_contributions(self, X):
        contributions = {}
        for name, model in self.models.items():
            contributions[name] = {
                'weight': self.weights[name],
                'probabilities': model.predict_proba(X)
            }
        return contributions
`

### Method 2: Stacking (Meta-Learner)

More powerful but requires careful temporal CV.

`python
class StackingEnsemble:
    def __init__(self, base_models: dict, meta_learner=None):
        self.base_models = base_models
        self.meta_learner = meta_learner or LogisticRegression(C=0.1, max_iter=1000)
        self.is_fitted = False
    
    def fit(self, X_train, y_train, X_val, y_val):
        for name, model in self.base_models.items():
            model.fit(X_train, y_train)
        
        meta_features = []
        for name, model in self.base_models.items():
            probs = model.predict_proba(X_val)
            meta_features.append(probs)
        
        meta_X = np.hstack(meta_features)
        self.meta_learner.fit(meta_X, y_val)
        self.is_fitted = True
        
        X_full = np.vstack([X_train, X_val])
        y_full = np.hstack([y_train, y_val])
        for name, model in self.base_models.items():
            model.fit(X_full, y_full)
    
    def predict_proba(self, X):
        if not self.is_fitted:
            raise ValueError('Call fit first')
        
        meta_features = []
        for name, model in self.base_models.items():
            probs = model.predict_proba(X)
            meta_features.append(probs)
        
        meta_X = np.hstack(meta_features)
        return self.meta_learner.predict_proba(meta_X)
`

### Method 3: Regime-Conditioned Ensemble

Different weights per market regime.

`python
class RegimeConditionedEnsemble:
    def __init__(self, models: dict, regime_model):
        self.models = models
        self.regime_model = regime_model
        self.regime_weights = {}
    
    def fit(self, X_train, y_train, X_val, y_val, regimes_val):
        val_probs = {}
        for name, model in self.models.items():
            val_probs[name] = model.predict_proba(X_val)
        
        for regime in [0, 1, 2]:
            mask = regimes_val == regime
            if mask.sum() < 100:
                self.regime_weights[regime] = {name: 1.0/len(self.models) for name in self.models}
                continue
            
            regime_probs = {name: probs[mask] for name, probs in val_probs.items()}
            regime_y = y_val[mask]
            
            losses = {name: log_loss(regime_y, probs) for name, probs in regime_probs.items()}
            inv_losses = {name: 1.0/loss for name, loss in losses.items()}
            total = sum(inv_losses.values())
            self.regime_weights[regime] = {name: w/total for name, w in inv_losses.items()}
    
    def predict_proba(self, X, regimes):
        probs = np.zeros((X.shape[0], 3))
        
        for regime in [0, 1, 2]:
            mask = regimes == regime
            if not mask.any():
                continue
            
            weights = self.regime_weights[regime]
            for name, model in self.models.items():
                model_probs = model.predict_proba(X[mask])
                probs[mask] += weights[name] * model_probs
        
        return probs
`

## Weight Determination: Leakage Prevention

### Critical Rules

1. Weights ONLY from validation data - Never test data
2. Per-fold weights - In walk-forward, each fold gets its own weights
3. No peeking - Test set predictions combined with fixed weights from validation
4. Stability check - Weights should be stable across folds

`python
def compute_walkforward_weights(models, folds):
    fold_weights = []
    
    for fold_idx, (X_train, y_train, X_val, y_val, X_test, y_test) in enumerate(folds):
        for name, model in models.items():
            model.fit(X_train, y_train)
        
        val_probs = {name: model.predict_proba(X_val) for name, model in models.items()}
        
        losses = {name: log_loss(y_val, probs) for name, probs in val_probs.items()}
        inv_losses = {name: 1.0/loss for name, loss in losses.items()}
        total = sum(inv_losses.values())
        weights = {name: w/total for name, w in inv_losses.items()}
        
        fold_weights.append(weights)
        
        test_probs = {name: model.predict_proba(X_test) for name, model in models.items()}
        ensemble_test = sum(weights[name] * probs for name, probs in test_probs.items())
        test_loss = log_loss(y_test, ensemble_test)
        
        print(f'Fold {fold_idx}: weights={weights}, test_logloss={test_loss:.4f}')
    
    weight_df = pd.DataFrame(fold_weights)
    print('Weight stability (std across folds):')
    print(weight_df.std())
    
    return fold_weights
`

## Model Diversity Requirements

For ensemble to work, base models must make different errors.

### Diversity Metrics

`python
def compute_diversity(preds_a, preds_b, y_true):
    pred_a = preds_a.argmax(axis=1)
    pred_b = preds_b.argmax(axis=1)
    disagreement = (pred_a != pred_b).mean()
    
    correct_a = (pred_a == y_true)
    correct_b = (pred_b == y_true)
    N = len(y_true)
    N11 = (correct_a & correct_b).sum()
    N00 = (~correct_a & ~correct_b).sum()
    N10 = (correct_a & ~correct_b).sum()
    N01 = (~correct_a & correct_b).sum()
    
    q_stat = (N11 * N00 - N10 * N01) / (N11 * N00 + N10 * N01 + 1e-10)
    prob_corr = np.corrcoef(preds_a.flatten(), preds_b.flatten())[0,1]
    
    return {
        'disagreement': disagreement,
        'q_statistic': q_stat,
        'prob_correlation': prob_corr
    }
`

### Target Diversity
- Disagreement rate: 15-30% (too low = redundant, too high = unstable)
- Q-statistic: < 0.7 (lower = more diverse)
- Probability correlation: < 0.85

### Ensuring Diversity
1. Different algorithms: XGBoost + LightGBM + RF (different inductive biases)
2. Different feature subsets: Technical only / Technical+Fundamental / Technical+News
3. Different hyperparameters: Different depth, learning rate, subsampling
4. Different random seeds: Bagging effect
5. Specialized models: Regime-specific, sector-specific

## Ensemble Configuration for v1

### Recommended Setup
`python
ensemble_config = {
    'base_models': {
        'xgb_tech': XGBClassifier(..., random_state=42),
        'xgb_fund': XGBClassifier(..., random_state=123),
        'xgb_news': XGBClassifier(..., random_state=456),
        'lgb_tech': LGBMClassifier(..., random_state=42),
        'rf_tech': RandomForestClassifier(..., random_state=42),
        'lr_all': LogisticRegression(..., random_state=42),
    },
    'ensemble_method': 'weighted_average',
    'weight_method': 'inv_logloss',
    'calibration': 'isotonic',
    'regime_conditioned': False,
}
`

### Why This Configuration?
- 6 diverse base models
- 3 algorithms (XGB, LGB, RF, LR)
- 3 feature variations (tech, tech+fund, tech+news)
- Weighted average = interpretable, fast, leakage-proof
- Calibration applied post-ensemble

## Probability Calibration for Ensemble

Calibrate AFTER ensemble, not before.

`python
from sklearn.calibration import CalibratedClassifierCV

# WRONG: Calibrate each model, then ensemble
# for name, model in models.items():
#     model = CalibratedClassifierCV(model, method='isotonic', cv=3)
# ensemble = WeightedAverage(models)

# RIGHT: Ensemble first, then calibrate
ensemble = WeightedAverageEnsemble(base_models)
ensemble.fit_weights(X_val, y_val)

calibrated_ensemble = CalibratedClassifierCV(ensemble, method='isotonic', cv='prefit')
calibrated_ensemble.fit(X_cal, y_cal)

# Use calibrated_ensemble for production
`

## Evaluation of Ensemble

`python
def evaluate_ensemble(ensemble, X_test, y_test, base_models):
    ens_probs = ensemble.predict_proba(X_test)
    ens_preds = ens_probs.argmax(axis=1)
    
    base_probs = {name: model.predict_proba(X_test) for name, model in base_models.items()}
    base_preds = {name: probs.argmax(axis=1) for name, probs in base_probs.items()}
    
    results = {
        'ensemble': compute_all_metrics(y_test, ens_probs, ens_preds),
        'base_models': {}
    }
    
    for name in base_models:
        results['base_models'][name] = compute_all_metrics(y_test, base_probs[name], base_preds[name])
    
    best_base = max(results['base_models'].items(), key=lambda x: x[1]['roc_auc_macro'])[0]
    
    comparison = compare_models(ens_probs, base_probs[best_base], y_test, lambda y, p: roc_auc_score(y, p, multi_class='ovr'))
    results['vs_best_base'] = comparison
    
    return results
`

## Summary

| Aspect | Decision |
|--------|----------|
| Primary Method | Weighted Average (probabilities) |
| Weight Optimization | Inverse validation log-loss |
| Calibration | Isotonic regression on ensemble (post-hoc) |
| Regime Conditioning | v2 (not v1) |
| Stacking | Research only (v2+) |
| Number of Base Models | 5-7 (diverse) |
| Diversity Target | Disagreement 15-30%, Q-stat < 0.7 |

Key Principle: Simpler ensemble that generalizes > Complex ensemble that overfits.