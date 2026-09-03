# 29_BENCHMARKS.md

## Benchmarks

This document defines benchmark strategies for fair comparison.

## Benchmark Strategies

### 1. Random Selection
- Randomly predict UP/DOWN/SIDEWAYS with equal probability
- Purpose: Absolute floor - any model must beat this
- Expected: 33% accuracy, log loss = 1.099, Brier = 0.444

### 2. Buy and Hold
- Always predict UP (or market direction)
- Purpose: Passive benchmark
- Expected: Accuracy = market UP%, log loss varies

### 3. Index Benchmark (SPY)
- Predict same as S&P 500 return direction
- Purpose: Market benchmark
- Comparison: Stock-specific model vs market beta

### 4. Simple Momentum Strategy
- Predict UP if 20-day return > 0, else DOWN
- Purpose: Classic technical baseline
- No ML, pure heuristic

### 5. Simple Moving Average Crossover
- Predict UP if SMA(20) > SMA(50), else DOWN
- Purpose: Classic trend-following baseline

### 6. Logistic Regression (ML Baseline)
- Regularized logistic regression on all features
- Purpose: Linear ML baseline
- All non-linear models must beat this

### 7. XGBoost (Primary ML Model)
- Tuned XGBoost on technical features
- Purpose: Primary production candidate

### 8. Ensemble (Best ML)
- Weighted average of XGBoost, LightGBM, RF
- Purpose: Best ML prediction

## Fair Comparison Protocol

1. **Same Data**: All benchmarks use identical train/val/test splits
2. **Same Horizons**: Evaluate at same prediction horizons (5, 20 days)
3. **Same Universe**: Same stock universe, same time periods
4. **Same Costs**: Backtest all with identical cost model
5. **Same Metrics**: Report all metrics for all benchmarks
6. **Statistical Tests**: Paired bootstrap tests for significance
7. **Multiple Periods**: Walk-forward with 5+ test periods

## Benchmark Results Template

| Strategy | Log Loss | Brier | ECE | ROC-AUC | Accuracy | Sharpe (net) | Max DD | Profit Factor |
|----------|----------|-------|-----|---------|----------|--------------|--------|---------------|
| Random | 1.099 | 0.444 | ~0.15 | 0.50 | 33% | N/A | N/A | N/A |
| Buy & Hold | - | - | - | - | - | - | - | - |
| Momentum | - | - | - | - | - | - | - | - |
| SMA Cross | - | - | - | - | - | - | - | - |
| Logistic Reg | - | - | - | - | - | - | - | - |
| XGBoost | - | - | - | - | - | - | - | - |
| Ensemble | - | - | - | - | - | - | - | - |

## Key Comparisons

### ML vs Heuristics
- Does XGBoost beat momentum/SMA on out-of-sample?
- Statistical significance required

### ML vs Linear
- Does XGBoost beat Logistic Regression?
- Justifies non-linear complexity

### Ensemble vs Single
- Does ensemble beat best single model?
- Justifies ensemble complexity

### Prediction vs Trading
- Good prediction metrics but bad trading?
- Analyze: calibration, threshold, sizing

## Minimum Benchmark Set for v1

For v1 release, MUST report against:
1. Random (sanity)
2. Buy-and-hold (passive)
3. Momentum (simple technical)
4. Logistic Regression (linear ML)
5. XGBoost (primary)
6. Ensemble (if applicable)

All on walk-forward test periods with bootstrap CIs.
