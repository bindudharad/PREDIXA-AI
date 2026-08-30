# 05_DATA_LEAKAGE_PREVENTION.md

## Data Leakage Prevention: Comprehensive Guide

This document is extremely important. Data leakage is the single biggest risk in financial ML. A model that appears to work due to leakage will fail catastrophically in production. Every team member must understand and enforce these rules.

## Types of Leakage

### 1. Look-Ahead Bias
Using information that would not be available at prediction time.

INCORRECT:
`python
# WRONG: Using future data to compute features
def compute_features(df):
    df[future_return_5d] = df[close].shift(-5) / df[close] - 1  # LEAKAGE!
    df[max_future_price_10d] = df[high].rolling(10).max().shift(-10)  # LEAKAGE!
    return df
`

CORRECT:
`python
# RIGHT: Only past and current data
def compute_features(df):
    df[return_1d] = df[close] / df[close].shift(1) - 1
    df[return_5d] = df[close] / df[close].shift(5) - 1
    df[max_past_price_10d] = df[high].rolling(10).max()  # Only past
    return df
`

### 2. Survivorship Bias
Only analyzing currently-listed stocks, ignoring delisted ones.

INCORRECT:
`python
# WRONG: Universe = current S&P 500 constituents
universe = get_sp500_constituents(today)  # Only survivors!
data = fetch_history(universe, start=2010-01-01)
`

CORRECT:
`python
# RIGHT: Use point-in-time universe
universe = get_sp500_constituents(as_of_date=2010-01-01)  # Historical composition
# Track delistings, include them until delisting date
data = fetch_history_with_delistings(universe, start=2010-01-01)
`

### 3. Future Data Contamination
Any future information leaking into training features.

INCORRECT:
`python
# WRONG: Normalizing using full dataset statistics
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_full)  # LEAKAGE! Uses test data statistics
`

CORRECT:
`python
# RIGHT: Fit scaler ONLY on training data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)  # Transform only
X_test_scaled = scaler.transform(X_test)
`

### 4. Incorrect Timestamp Alignment
Misaligned timestamps causing future data to appear current.

INCORRECT:
`python
# WRONG: Using daily close for intraday prediction
# If predicting at 10:00 AM, close of today is NOT available
features = compute_features(daily_data)  # Includes today's close
prediction = model.predict(features)  # LEAKAGE!
`

CORRECT:
`python
# RIGHT: Explicit prediction timestamp
prediction_time = pd.Timestamp(2024-01-15 10:00:00, tz=US/Eastern)
# Features must use data with timestamp < prediction_time
features = compute_features_as_of(daily_data, prediction_time - 1 day)  # Yesterday's close
`

### 5. Improper Normalization/Standardization
Using global statistics instead of expanding/rolling window statistics.

INCORRECT:
`python
# WRONG: Global z-score uses future data
df[zscore] = (df[close] - df[close].mean()) / df[close].std()
`

CORRECT:
`python
# RIGHT: Expanding window (only past data)
df[zscore_expanding] = (df[close] - df[close].expanding().mean()) / df[close].expanding().std()

# OR: Rolling window (fixed lookback)
df[zscore_rolling_252] = (df[close] - df[close].rolling(252).mean()) / df[close].rolling(252).std()
`

### 6. Future News Leakage
Using news published after prediction time.

INCORRECT:
`python
# WRONG: News from day T used to predict day T
daily_news = fetch_news(date=2024-01-15)
sentiment = analyze_sentiment(daily_news)
predict_return(2024-01-15, sentiment)  # LEAKAGE! News during day not available at open
`

CORRECT:
`python
# RIGHT: News with strict cutoff
# Prediction at market open (9:30 AM) -> only news before 9:30 AM
# Prediction at market close (4:00 PM) -> only news before 4:00 PM
cutoff_time = prediction_timestamp - timedelta(hours=1)  # Conservative buffer
news = fetch_news(before=cutoff_time)
sentiment = analyze_sentiment(news)
`

### 7. Corporate Action Leakage
Using split/dividend info before it is announced.

INCORRECT:
`python
# WRONG: Adjusting prices with future split knowledge
# If split announced Jan 15, effective Jan 20
# On Jan 18, we should NOT know about the split
adjusted_price = apply_split(raw_price, split_ratio)  # LEAKAGE on Jan 18!
`

CORRECT:
`python
# RIGHT: Only adjust when action is PUBLICLY ANNOUNCED
announcement_date = get_split_announcement_date(symbol, split_date)
if prediction_date >= announcement_date:
    adjusted_price = apply_split(raw_price, split_ratio)
else:
    adjusted_price = raw_price  # No adjustment yet
`

### 8. Label Leakage in Feature Engineering
Using the target variable (or proxy) as a feature.

INCORRECT:
`python
# WRONG: Target leakage
df[target] = (df[close].shift(-5) / df[close] - 1 > 0.02).astype(int)
df[feature_1] = df[target].rolling(5).mean()  # LEAKAGE! Target used as feature
`

CORRECT:
`python
# RIGHT: Features completely independent of target
df[feature_1] = df[close].rolling(5).mean() / df[close] - 1  # Past returns only
df[target] = (df[close].shift(-5) / df[close] - 1 > 0.02).astype(int)
`

## Leakage Prevention Checklist (Enforce at Every Stage)

### Data Ingestion
- [ ] Raw data stored with original timestamps (no modification)
- [ ] Corporate actions applied with announcement date awareness
- [ ] Multiple data sources cross-validated
- [ ] Data quality reports generated per ingestion run

### Feature Engineering
- [ ] All features computed with timestamp <= prediction_timestamp
- [ ] No shift(-n) or rolling().shift(-n) operations
- [ ] Expanding/rolling windows only look backward
- [ ] Fundamental data lagged by at least 60 days (earnings announcement delay)
- [ ] News sentiment lagged by at least 1 day (conservative)
- [ ] Macro data lagged by at least 1 day
- [ ] Feature computation code identical for training and inference

### Label Generation
- [ ] Labels computed from FUTURE returns only (forward-looking)
- [ ] Entry price = close of prediction date (or next open, explicitly defined)
- [ ] Exit price = close of prediction date + horizon
- [ ] Labels NEVER used in feature computation
- [ ] Label generation code separate from feature code

### Dataset Construction
- [ ] Train/validation/test splits respect TEMPORAL ORDERING
- [ ] NO random shuffling of time-series data
- [ ] Purged/embargoed gaps between train/val/test (e.g., 5-30 days)
- [ ] Expanding window or rolling window only
- [ ] Dataset version hash includes split configuration

### Model Training
- [ ] Scalers/encoders fit ONLY on training data
- [ ] Hyperparameter tuning uses validation set ONLY (not test)
- [ ] Cross-validation uses temporal splits (TimeSeriesSplit)
- [ ] Early stopping monitored on validation set
- [ ] No feature selection using test set performance

### Model Evaluation
- [ ] Test set NEVER touched during development
- [ ] Walk-forward validation with multiple test periods
- [ ] Metrics reported with confidence intervals (bootstrap)
- [ ] Performance decomposed by market regime

### Production Inference
- [ ] Feature store serves features at exact prediction timestamp
- [ ] Online features = offline features (consistency check)
- [ ] Model version pins feature version
- [ ] Prediction logged BEFORE outcome known
- [ ] Drift detection on feature distributions

## Concrete Examples: Leakage vs. Correct

### Example 1: Rolling Volatility
`python
# LEAKAGE - Uses future data in rolling window
df[vol_20d_leak] = df[returns].rolling(20).std().shift(-10)

# CORRECT - Only past data
df[vol_20d] = df[returns].rolling(20).std()  # Ends at current row
`

### Example 2: Relative Strength vs Index
`python
# LEAKAGE - Index return includes today's close (if predicting at open)
df[rel_strength_leak] = df[stock_return_1d] - df[spy_return_1d]

# CORRECT - Use lagged index return
df[rel_strength] = df[stock_return_1d] - df[spy_return_1d].shift(1)
`

### Example 3: Fundamental Data
`python
# LEAKAGE - Using earnings announced today to predict today
df[pe_ratio_leak] = df[close] / df[eps]  # EPS might be announced today!

# CORRECT - Lag fundamentals by reporting lag
df[pe_ratio] = df[close] / df[eps].shift(60)  # 60-day conservative lag
`

### Example 4: Target Encoding
`python
# LEAKAGE - Target encoding using full dataset
df[sector_target_mean] = df.groupby(sector)[target].transform(mean)

# CORRECT - Expanding target encoding (only past targets)
df[sector_target_mean_expanding] = df.groupby(sector)[target].expanding().mean().reset_index(level=0, drop=True).shift(1)
`

### Example 5: Cross-Validation
`python
# LEAKAGE - Random K-fold on time series
kf = KFold(n_splits=5, shuffle=True)  # WRONG!

# CORRECT - Time series split with embargo
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5, gap=30)  # 30-day embargo
`

## Automated Leakage Detection

Implement these checks in CI/CD pipeline:

`python
def detect_leakage(features_df, labels_df, prediction_timestamps):
    Automated leakage detection checks.
    issues = []
    
    # Check 1: Feature timestamp <= prediction timestamp
    for col in features_df.columns:
        if features_df[col].index.max() > prediction_timestamps.max():
            issues.append(f Feature {col} has future data)
    
    # Check 2: No target in features
    target_cols = [c for c in features_df.columns if target in c.lower() or label in c.lower()]
    if target_cols:
        issues.append(f Potential target columns in features: {target_cols})
    
    # Check 3: Correlation with future returns (proxy for leakage)
    future_returns = labels_df[future_return_5d]
    for col in features_df.select_dtypes(include=[np.number]).columns:
        corr = features_df[col].corr(future_returns)
        if abs(corr) > 0.3:  # Suspiciously high
            issues.append(f High correlation with future return: {col}={corr:.3f})
    
    # Check 4: Expanding window statistics
    for col in features_df.columns:
        if expanding in col.lower() or cumsum in col.lower():
            # Verify it only uses past
            pass  # Implementation specific
    
    return issues
`

## Leakage Testing Protocol

Before ANY model goes to production:

1. **Temporal Holdout Test**: Train on 2018-2021, validate 2022, test 2023. No overlap.
2. **Purged CV**: 30-day gap between train/val folds.
3. **Feature Importance Stability**: Top features should be stable across folds.
4. **Permutation Test**: Shuffle labels; model should perform at chance level.
5. **Future Leakage Probe**: Add synthetic future feature; model should NOT use it.
6. **Walk-Forward Consistency**: Performance should not spike at fold boundaries.

## Code Architecture for Leakage Prevention

`python
# Enforce at module level
class TemporalFeatureComputer:
    def __init__(self, prediction_timestamp: pd.Timestamp):
        self.prediction_timestamp = prediction_timestamp
        self.cutoff = prediction_timestamp  # Features can only use data <= cutoff
    
    def compute(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        # Filter raw data to only include timestamps <= cutoff
        available_data = raw_data[raw_data.index <= self.cutoff]
        # Compute features
        features = self._compute_features(available_data)
        # Verify no future data
        assert features.index.max() <= self.cutoff
        return features

class TemporalLabelGenerator:
    def __init__(self, horizon_days: int, threshold: float):
        self.horizon = horizon_days
        self.threshold = threshold
    
    def generate(self, price_data: pd.DataFrame) -> pd.DataFrame:
        # Entry: close at prediction date
        # Exit: close at prediction date + horizon
        # This is FORWARD-LOOKING by design (labels are targets)
        labels = self._compute_forward_returns(price_data)
        return labels

# Usage - STRICT SEPARATION
feature_computer = TemporalFeatureComputer(prediction_timestamp=2024-01-15)
features = feature_computer.compute(raw_ohlcv)

label_generator = TemporalLabelGenerator(horizon_days=5, threshold=0.02)
labels = label_generator.generate(raw_ohlcv)  # Uses FUTURE data - OK for labels!

# Features and labels aligned by prediction_date
dataset = align_features_labels(features, labels, on=prediction_date)
`

## Summary: Golden Rules

1. **TIMESTAMP DISCIPLINE**: Every data point has a timestamp. Features timestamp <= prediction timestamp. Labels timestamp > prediction timestamp.

2. **CODE SEPARATION**: Feature code != Label code. Different modules, different tests.

3. **VERSION PINNING**: Model version -> Feature version -> Data version. Immutable chain.

4. **EXPANDING WINDOWS ONLY**: No rolling windows that peek forward. No global statistics.

5. **LAG EVERYTHING EXTERNAL**: Fundamentals (60d), News (1d), Macro (1d), Corporate actions (announcement date).

6. **SURVIVORSHIP TRACKING**: Every delisted stock tracked with delisting date and reason.

7. **AUTOMATED CHECKS**: Leakage detection in CI/CD. No exceptions.

8. **AUDIT TRAIL**: Every prediction logged with feature hash, model version, timestamp.

REMEMBER: A model with leakage will show amazing backtest results and lose money in production. The cost of preventing leakage is near zero; the cost of not preventing it is everything.