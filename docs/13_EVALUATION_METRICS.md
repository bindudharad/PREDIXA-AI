# 13_EVALUATION_METRICS.md

## Evaluation Metrics

This document defines all metrics for evaluating both prediction quality and trading performance.

## Metric Categories

`mermaid
flowchart TD
    subgraph ML [ML Metrics - Prediction Quality]
        ML1[Classification
Accuracy, Precision, Recall, F1]
        ML2[Probabilistic
Log Loss, Brier, ECE, MCE]
        ML3[Ranking
ROC-AUC, PR-AUC]
        ML4[Calibration
Reliability Diagrams]
    end
    
    subgraph Trading [Trading Metrics - P&L Quality]
        TR1[Returns
Total, CAGR, Risk-Adjusted]
        TR2[Risk
Sharpe, Sortino, Max DD]
        TR3[Trade Stats
Win Rate, Expectancy, PF]
        TR4[Costs
Turnover, Cost Drag]
    end
    
    ML1 --> TR1
    ML2 --> TR1
    ML3 --> TR1
    ML4 --> TR1
`

---

## ML Metrics (Prediction Quality)

### Primary Metrics (Optimization Targets)

#### 1. Log Loss (Cross-Entropy) - PRIMARY
`python
from sklearn.metrics import log_loss

# y_true: (n,) class indices [0, 1, 2]
# y_prob: (n, 3) probabilities summing to 1
logloss = log_loss(y_true, y_prob)

# Lower is better. Perfect = 0. Random (3-class) = 1.099
# Primary optimization target for training and HPO
`

**Why Log Loss?**
- Proper scoring rule (incentivizes honest probabilities)
- Sensitive to confidence: confident wrong predictions penalized heavily
- Directly relates to calibration quality

#### 2. Brier Score - PRIMARY
`python
def brier_score(y_true, y_prob):
    # Mean squared error between predicted probs and one-hot labels
    n_classes = y_prob.shape[1]
    y_onehot = np.eye(n_classes)[y_true]
    return np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1))

# Range: [0, 2]. Lower better. Random (3-class) = 0.444
# Decomposable: Reliability + Resolution + Uncertainty
`

**Why Brier Score?**
- Proper scoring rule
- Decomposable into calibration (reliability) and discrimination (resolution)
- Interpretable as MSE of probabilities

#### 3. Expected Calibration Error (ECE) - PRIMARY
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

# Target: < 0.02 (excellent), < 0.05 (acceptable)
`

**Why ECE?**
- Measures calibration: do predicted probabilities match observed frequencies?
- Weighted by bin frequency (unlike MCE)
- Directly actionable: high ECE means recalibrate

### Secondary Metrics (Diagnostic)

#### 4. Maximum Calibration Error (MCE)
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

# Target: < 0.05 (excellent), < 0.10 (acceptable)
# Worst-case calibration error
`

#### 5. ROC-AUC (One-vs-Rest)
`python
from sklearn.metrics import roc_auc_score

# Macro average across classes
roc_auc_macro = roc_auc_score(y_true, y_prob, multi_class='ovr', average='macro')
roc_auc_ovo = roc_auc_score(y_true, y_prob, multi_class='ovo', average='macro')

# Per-class
roc_auc_per_class = roc_auc_score(y_true, y_prob, multi_class='ovr', average=None)

# Target: > 0.55 (better than random), > 0.60 (useful)
`

#### 6. PR-AUC (Precision-Recall AUC)
`python
from sklearn.metrics import average_precision_score

pr_auc_macro = average_precision_score(y_true, y_prob, average='macro')
pr_auc_per_class = average_precision_score(y_true, y_prob, average=None)

# Better than ROC-AUC for imbalanced classes
`

#### 7. Classification Metrics (Per-Class)
`python
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Macro averages (equal weight per class)
precision_macro = precision_score(y_true, y_pred, average='macro')
recall_macro = recall_score(y_true, y_pred, average='macro')
f1_macro = f1_score(y_true, y_pred, average='macro')

# Per-class (critical for understanding which class works)
precision_per_class = precision_score(y_true, y_pred, average=None)
recall_per_class = recall_score(y_true, y_pred, average=None)
f1_per_class = f1_score(y_true, y_pred, average=None)

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
# [[TN, FP, FN], [FP, TN, FN], [FN, FP, TN]] for 3-class
`

### Metric Targets Summary (v1)

| Metric | Random Baseline | Minimum Acceptable | Target | Excellent |
|--------|-----------------|-------------------|--------|-----------|
| Log Loss (3-class) | 1.099 | < 1.10 | < 0.90 | < 0.80 |
| Brier Score | 0.444 | < 0.40 | < 0.30 | < 0.25 |
| ECE | ~0.15 | < 0.05 | < 0.02 | < 0.01 |
| MCE | ~0.30 | < 0.10 | < 0.05 | < 0.03 |
| ROC-AUC (macro) | 0.50 | > 0.55 | > 0.58 | > 0.62 |
| PR-AUC (macro) | ~0.33 | > 0.35 | > 0.40 | > 0.45 |
| Accuracy | 33% | > 38% | > 42% | > 45% |
| F1 (macro) | 33% | > 35% | > 40% | > 43% |

---

## Trading Metrics (P&L Quality)

### Return Metrics

#### 1. Total Return
`python
total_return = (final_value - initial_capital) / initial_capital
`

#### 2. Compound Annual Growth Rate (CAGR)
`python
def cagr(equity_curve, trading_days_per_year=252):
    n_years = len(equity_curve) / trading_days_per_year
    return (equity_curve[-1] / equity_curve[0]) ** (1 / n_years) - 1
`

#### 3. Annualized Volatility
`python
def annualized_vol(daily_returns, trading_days=252):
    return daily_returns.std() * np.sqrt(trading_days)
`

### Risk-Adjusted Returns

#### 4. Sharpe Ratio - PRIMARY TRADING METRIC
`python
def sharpe_ratio(daily_returns, risk_free_rate=0.0, trading_days=252):
    excess_returns = daily_returns - risk_free_rate / trading_days
    return np.sqrt(trading_days) * excess_returns.mean() / excess_returns.std()

# Target: > 1.0 (acceptable), > 1.5 (good), > 2.0 (excellent)
# MUST be computed on NET returns (after all costs)
`

#### 5. Sortino Ratio
`python
def sortino_ratio(daily_returns, risk_free_rate=0.0, trading_days=252):
    excess_returns = daily_returns - risk_free_rate / trading_days
    downside_returns = excess_returns[excess_returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(trading_days)
    return np.sqrt(trading_days) * excess_returns.mean() / downside_vol

# Only penalizes downside volatility
# Target: > 1.5 (good)
`

#### 6. Calmar Ratio
`python
def calmar_ratio(equity_curve, trading_days=252):
    cagr_val = cagr(equity_curve, trading_days)
    max_dd = max_drawdown(equity_curve)
    return cagr_val / abs(max_dd) if max_dd != 0 else np.inf

# Return per unit of max drawdown
# Target: > 1.0
`

### Drawdown Metrics

#### 7. Maximum Drawdown
`python
def max_drawdown(equity_curve):
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

# Target: < 20% (acceptable), < 10% (good)
`

#### 8. Max Drawdown Duration
`python
def max_drawdown_duration(equity_curve):
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    in_dd = drawdown < 0
    # Find longest consecutive True sequence
    dd_periods = (in_dd != in_dd.shift()).cumsum()
    durations = in_dd.groupby(dd_periods).sum()
    return durations.max() if durations.any() else 0

# Target: < 12 months
`

#### 9. Ulcer Index
`python
def ulcer_index(equity_curve):
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    return np.sqrt(np.mean(drawdown ** 2))

# RMS of drawdowns - captures depth and duration
# Target: < 0.05
`

### Trade-Level Metrics

#### 10. Win Rate
`python
win_rate = (trades_pnl > 0).mean()
# Target: > 50% (but depends on avg win/loss ratio)
`

#### 11. Average Win / Average Loss
`python
avg_win = trades_pnl[trades_pnl > 0].mean()
avg_loss = abs(trades_pnl[trades_pnl < 0].mean())
win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf
`

#### 12. Profit Factor
`python
profit_factor = trades_pnl[trades_pnl > 0].sum() / abs(trades_pnl[trades_pnl < 0].sum())
# Target: > 1.2 (acceptable), > 1.5 (good), > 2.0 (excellent)
`

#### 13. Expectancy
`python
expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss
# Expected profit per trade
# Target: > 0 (positive), > 0.5% of capital (good)
`

#### 14. Kelly Criterion (Optimal Leverage)
`python
def kelly_fraction(win_rate, win_loss_ratio):
    return win_rate - (1 - win_rate) / win_loss_ratio
# Optimal fraction of capital to risk per trade
`

### Cost Metrics

#### 15. Turnover
`python
def turnover(daily_weights, trading_days=252):
    # daily_weights: (n_days, n_assets) portfolio weights
    weight_changes = np.abs(daily_weights.diff()).sum(axis=1)
    annual_turnover = weight_changes.mean() * trading_days
    return annual_turnover

# Target: < 200% annually (manageable)
`

#### 16. Cost Drag
`python
cost_drag_bps = (total_costs / avg_portfolio_value) * 10000
# Total costs as basis points of portfolio per year
# Target: < 50 bps/year
`

---

## Metric Hierarchy

`mermaid
flowchart TD
    A[Primary: Log Loss + Brier + ECE] --> B{Pass Thresholds?}
    B -->|No| C[Reject Model]
    B -->|Yes| D[Secondary: ROC-AUC, PR-AUC, F1]
    D --> E{Pass Thresholds?}
    E -->|No| F[Investigate - May Still Trade]
    E -->|Yes| G[Trading Metrics: Sharpe, Sortino, MaxDD]
    G --> H{Positive After Costs?}
    H -->|No| I[Reject - No Edge After Costs]
    H -->|Yes| J[Paper Trading Candidate]
`

### Decision Rules

| Stage | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| 1 | Log Loss | < 1.10 | Continue |
| 1 | Brier | < 0.40 | Continue |
| 1 | ECE | < 0.05 | Continue |
| 2 | ROC-AUC | > 0.55 | Continue |
| 2 | F1 macro | > 35% | Continue |
| 3 | Sharpe (net) | > 1.0 | Paper Trade |
| 3 | Max DD | < 20% | Paper Trade |
| 3 | Profit Factor | > 1.2 | Paper Trade |

---

## Statistical Significance

### Bootstrap Confidence Intervals
`python
def bootstrap_ci(metric_fn, y_true, y_pred, n_bootstrap=1000, alpha=0.05):
    n = len(y_true)
    boot_values = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        boot_values.append(metric_fn(y_true[idx], y_pred[idx]))
    
    lower = np.percentile(boot_values, 100 * alpha / 2)
    upper = np.percentile(boot_values, 100 * (1 - alpha / 2))
    return np.mean(boot_values), (lower, upper)
`

### Paired Bootstrap Test (Model Comparison)
`python
def paired_bootstrap_test(metric_fn, y_true, preds_a, preds_b, n_bootstrap=1000):
    n = len(y_true)
    diffs = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        m_a = metric_fn(y_true[idx], preds_a[idx])
        m_b = metric_fn(y_true[idx], preds_b[idx])
        diffs.append(m_a - m_b)
    
    ci = (np.percentile(diffs, 2.5), np.percentile(diffs, 97.5))
    p_value = (np.array(diffs) <= 0).mean()
    
    return {
        'mean_diff': np.mean(diffs),
        'ci_95': ci,
        'p_value': p_value,
        'significant': ci[0] > 0  # A significantly better than B
    }
`

---

## Regime-Conditional Metrics

`python
def regime_conditional_metrics(y_true, y_prob, y_pred, regimes):
    # regimes: 0=bear, 1=sideways, 2=bull
    results = {}
    for regime in [0, 1, 2]:
        mask = regimes == regime
        if mask.sum() < 50:
            continue
        results[f'regime_{regime}'] = {
            'n_samples': mask.sum(),
            'log_loss': log_loss(y_true[mask], y_prob[mask]),
            'accuracy': accuracy_score(y_true[mask], y_pred[mask]),
            'roc_auc': roc_auc_score(y_true[mask], y_prob[mask], multi_class='ovr'),
            'ece': expected_calibration_error(y_true[mask], y_prob[mask]),
        }
    return results
`

**Why?** A model may work in bull markets but fail in bear markets. Must know.

---

## Reporting Template

`markdown
## Model Evaluation Report: {model_version}

### ML Metrics (Test Set)
| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Log Loss | X.XXX | < 0.90 | Yes/No |
| Brier Score | X.XXX | < 0.30 | Yes/No |
| ECE | X.XXX | < 0.02 | Yes/No |
| MCE | X.XXX | < 0.05 | Yes/No |
| ROC-AUC (macro) | X.XXX | > 0.58 | Yes/No |
| PR-AUC (macro) | X.XXX | > 0.40 | Yes/No |
| Accuracy | X.XX% | > 42% | Yes/No |
| F1 (macro) | X.XX% | > 40% | Yes/No |

### Per-Class Metrics
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| UP | X.XX | X.XX | X.XX | N |
| SIDEWAYS | X.XX | X.XX | X.XX | N |
| DOWN | X.XX | X.XX | X.XX | N |

### Calibration
- Reliability Diagram: [attached]
- ECE: X.XXX
- MCE: X.XXX

### Trading Metrics (Walk-Forward Backtest)
| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Sharpe (net) | X.XX | > 1.0 | Yes/No |
| Sortino | X.XX | > 1.5 | Yes/No |
| Max Drawdown | X.XX% | < 20% | Yes/No |
| CAGR (net) | X.XX% | > 5% | Yes/No |
| Profit Factor | X.XX | > 1.2 | Yes/No |
| Win Rate | X.XX% | > 45% | Yes/No |
| Expectancy | X.XX% | > 0 | Yes/No |
| Turnover | X.XX | < 200% | Yes/No |
| Cost Drag | X bps | < 50 | Yes/No |

### Regime-Conditional
| Regime | Log Loss | Accuracy | ROC-AUC | ECE |
|--------|----------|----------|---------|-----|
| Bear | X.XXX | X.XX% | X.XXX | X.XXX |
| Sideways | X.XXX | X.XX% | X.XXX | X.XXX |
| Bull | X.XXX | X.XX% | X.XXX | X.XXX |

### Statistical Significance
- vs Random: p = X.XXX
- vs Logistic Regression: p = X.XXX
- Bootstrap CI (Log Loss): [X.XXX, X.XXX]

### Conclusion
- ML Metrics Pass: Yes/No
- Trading Metrics Pass: Yes/No
- Ready for Paper Trading: Yes/No
- Key Risks: [list]
