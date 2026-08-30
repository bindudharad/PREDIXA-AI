# 06_PREDICTION_DEFINITION.md

## Prediction Problem Definition

This document mathematically defines the prediction problem, including horizons, return calculations, thresholds, label generation, and timestamp conventions.

## Mathematical Formulation

### Basic Return Calculation

Let:
- P(t) = Price at time t (close price of trading day t)
- P(t+n) = Price at time t+n (close price of trading day t+n)
- n = Prediction horizon in trading days

**Simple Return:**
R(t, t+n) = (P(t+n) - P(t)) / P(t) = P(t+n)/P(t) - 1

**Log Return:**
r(t, t+n) = ln(P(t+n)/P(t)) = ln P(t+n) - ln P(t)

### Prediction Horizon

We define multiple horizons for different use cases:

| Horizon | Trading Days | Calendar Days (approx) | Use Case |
|---------|--------------|------------------------|----------|
| H1 | 1 | 1-3 | Very short-term, high frequency |
| H5 | 5 | 7 | Weekly (primary) |
| H10 | 10 | 14 | Bi-weekly |
| H20 | 20 | 30 | Monthly (primary) |
| H60 | 60 | 90 | Quarterly

**Primary horizons for v1: H5 (5 days) and H20 (20 days)**

### Why These Horizons?

1. **H5 (1 week)**: Captures short-term momentum/mean-reversion; high sample count for training; manageable transaction costs
2. **H20 (1 month)**: Captures medium-term trends; lower noise; aligns with earnings cycles; realistic for position holding

**Tradeoffs:**
- Shorter horizon -> more samples, higher noise, higher turnover, higher costs
- Longer horizon -> fewer samples, lower noise, lower turnover, regime risk
- We avoid H1 (too noisy, microstructure effects) and H60+ (too few samples, regime changes)

### Classification Labels

#### 3-Class Problem (Primary)
y(t) = 2 if R(t, t+n) > theta_up (UP)
       1 if |R(t, t+n)| <= theta_side (SIDEWAYS)
       0 if R(t, t+n) < -theta_down (DOWN)

#### 2-Class Problem (Secondary)
y(t) = 1 if R(t, t+n) > 0 (PROFITABLE)
       0 if R(t, t+n) <= 0 (NOT_PROFITABLE)

### Threshold Selection

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| theta_up | 2% (0.02) | Meaningful move above noise; ~1x daily vol for typical stock |
| theta_down | 2% (0.02) | Symmetric for balanced classes |
| theta_side | 1% (0.01) | Narrow sideways band; captures true sideways |

**Why 2%?**
- Typical daily volatility for liquid stocks: 1.5-2.5%
- 2% ~ 1 standard deviation of 5-day return
- Below 1%: mostly noise, hard to predict
- Above 3%: too rare, class imbalance
- 2% balances signal detection with sample size

**Sensitivity Analysis Required:**
- Test thresholds: 1%, 1.5%, 2%, 2.5%, 3%
- Report class distribution for each
- Choose based on: class balance, prediction stability, backtest Sharpe

### Entry and Exit Timing

| Event | Timestamp | Price Used |
|-------|-----------|------------|
| Prediction Made | t_pred = Close of day T (16:00 ET) | N/A |
| Entry | t_entry = Close of day T (same as prediction) | P(T) = Close price day T |
| Exit | t_exit = Close of day T+n | P(T+n) = Close price day T+n |

**Alternative Entry (for backtesting):**
- Next-day open: P_open(T+1)
- Next-day VWAP: VWAP(T+1)
- **Default**: Close-to-close (simpler, more conservative)

### Label Generation Algorithm

`python
def generate_labels(prices, horizon, thresh_up=0.02, thresh_down=0.02, thresh_side=0.01):
    # Forward return: close(t+horizon) / close(t) - 1
    prices = prices.sort_values([symbol, date])
    prices[future_price] = prices.groupby(symbol)[close].shift(-horizon)
    prices[future_return] = prices[future_price] / prices[close] - 1
    
    # 3-class labels
    conditions = [
        prices[future_return] > thresh_up,
        prices[future_return] < -thresh_down,
    ]
    choices = [2, 0]  # UP=2, DOWN=0
    prices[label_3class] = np.select(conditions, choices, default=1)  # SIDEWAYS=1
    
    # 2-class labels
    prices[label_2class] = (prices[future_return] > 0).astype(int)
    
    # Clean: remove rows where future_price is NaN (end of series)
    prices = prices.dropna(subset=[future_price])
    
    # Rename date to prediction_date
    prices = prices.rename(columns={date: prediction_date})
    
    return prices[[symbol, prediction_date, label_3class, label_2class, future_return]]
`

### Timestamp Definitions

| Term | Definition | Example |
|------|------------|---------|
| Prediction Timestamp | When prediction is generated | 2024-01-15 16:00:00 ET (market close) |
| Feature Timestamp | Latest data used for features | 2024-01-15 16:00:00 ET (same as prediction) |
| Entry Timestamp | When position would be entered | 2024-01-15 16:00:00 ET (close) |
| Exit Timestamp | When position would be exited | 2024-01-22 16:00:00 ET (close, H5) |
| Label Timestamp | When outcome is known | 2024-01-22 16:00:00 ET (same as exit) |
| Outcome Timestamp | When P&L is realized | 2024-01-22 16:00:00 ET |

### Prediction Horizon vs. Data Availability

| Horizon | Prediction Date | Earliest Outcome Date | Data Needed Until |
|---------|-----------------|----------------------|-------------------|
| H5 | 2024-01-15 | 2024-01-22 | 2024-01-22 |
| H20 | 2024-01-15 | 2024-02-12 | 2024-02-12 |

**Critical**: Labels for prediction date T require data up to T+n. This means:
- Training data must END at least n days before validation start
- Test set must have n days of future data after last prediction
- Live prediction: outcome unknown until T+n

### Class Distribution Expectations

For H5 with 2% thresholds (typical US large caps):
| Class | Expected % | Rationale |
|-------|------------|-----------|
| UP | ~25-30% | Positive drift + volatility |
| SIDEWAYS | ~30-40% | Within +-1-2% band |
| DOWN | ~25-30% | Symmetric to UP |

For H20 with 2% thresholds:
| Class | Expected % | Rationale |
|-------|------------|-----------|
| UP | ~35-45% | Positive drift compounds |
| SIDEWAYS | ~15-25% | Wider distribution |
| DOWN | ~30-40% | Less symmetric at longer horizon |

**Actual distribution MUST be computed from data and reported per experiment.**

### Multi-Horizon Prediction

System supports simultaneous prediction at multiple horizons:
- Model can be horizon-specific (separate model per horizon)
- Or multi-output (single model predicts all horizons)
- **v1**: Separate models per horizon (simpler, more interpretable)

### Return Calculation Variations

| Variant | Formula | Use Case |
|---------|---------|----------|
| Close-to-Close | (C_t+n - C_t) / C_t | Primary (default) |
| Open-to-Close | (C_t+n - O_t+1) / O_t+1 | Next-day entry |
| Close-to-Open | (O_t+n - C_t) / C_t | Overnight |
| VWAP-to-VWAP | (VWAP_t+n - VWAP_t+1) / VWAP_t+1 | Institutional |

**v1 uses Close-to-Close exclusively.** Others added only if justified by backtest.

### Adjustment for Corporate Actions

All prices **must be split-adjusted and dividend-adjusted (total return)** before return calculation:

P_adj(t) = P_raw(t) / cum_split_factor(t) + cum_div_adjustment(t)

R(t, t+n) = P_adj(t+n) / P_adj(t) - 1

**Failure to adjust = look-ahead bias** (future splits/dividends not known at t).

### Label Quality Checks

Before training, validate labels:
1. **No NaN labels** in training period
2. **Class balance** within expected ranges
3. **No future leakage**: label at t only uses prices > t
4. **Consistency**: 2-class label = (3-class label != DOWN)
5. **Stationarity check**: Class distribution stable across years (if not, regime conditioning needed)

### Summary of Key Parameters

| Parameter | Default Value | Configurable | Notes |
|-----------|---------------|--------------|-------|
| Primary Horizons | 5, 20 days | Yes | H1, H10, H60 optional |
| UP Threshold | 2% | Yes | Test 1-3% |
| DOWN Threshold | 2% | Yes | Symmetric default |
| SIDEWAYS Band | +-1% | Yes | Within +-threshold |
| Entry Price | Close | Yes | Open/VWAP alternatives |
| Exit Price | Close | Yes | Fixed at horizon |
| Price Type | Total Return Adjusted | No | Mandatory |
| Frequency | Daily | No | Intraday not in v1 |