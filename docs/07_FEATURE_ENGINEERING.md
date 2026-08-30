# 07_FEATURE_ENGINEERING.md

## Feature Engineering Design Document

This document defines all feature groups, their computations, and critical leakage prevention rules. Features are organized by category with explicit availability timestamps.

## Feature Design Principles

1. **Temporal Integrity**: Every feature computed using ONLY data with timestamp less than or equal to prediction_timestamp
2. **Reproducibility**: Same code for training and inference (feature store)
3. **Versioning**: Feature set versioned with code hash + config hash
4. **Documentation**: Every feature has definition, formula, and availability lag
5. **No Target Leakage**: Features never use label information

## Feature Groups Overview

| Group | Count | Primary Data Source | Lag Required |
|-------|-------|---------------------|--------------|
| Price Features | ~15 | OHLCV | 0 days (close available) |
| Technical Indicators | ~25 | OHLCV | 0 days |
| Volatility Features | ~10 | OHLCV | 0 days |
| Market-Relative | ~10 | OHLCV + Indices | 1 day (index close) |
| Market Regime | ~8 | OHLCV + Macro | 1 day |
| Fundamental | ~15 | Financial Statements | 60 days (conservative) |
| News/Sentiment | ~10 | News Articles | 1 day |
| Macro | ~8 | Economic Data | 1 day |

**Total: ~101 features (expandable)**

---

## 1. Price Features

All computed from adjusted OHLCV. Available at market close (16:00 ET).

| Feature | Formula | Description | Lookback |
|---------|---------|-------------|----------|
| return_1d | C_t / C_{t-1} - 1 | 1-day simple return | 1 |
| return_5d | C_t / C_{t-5} - 1 | 5-day return | 5 |
| return_10d | C_t / C_{t-10} - 1 | 10-day return | 10 |
| return_20d | C_t / C_{t-20} - 1 | 20-day return | 20 |
| log_return_1d | ln(C_t / C_{t-1}) | 1-day log return | 1 |
| log_return_5d | ln(C_t / C_{t-5}) | 5-day log return | 5 |
| momentum_5d | C_t / C_{t-5} - 1 | Price momentum (same as return_5d) | 5 |
| momentum_20d | C_t / C_{t-20} - 1 | Medium-term momentum | 20 |
| gap_up | (O_t - C_{t-1}) / C_{t-1} | Overnight gap up | 1 |
| gap_down | (C_{t-1} - O_t) / C_{t-1} | Overnight gap down | 1 |
| hl_range | (H_t - L_t) / C_t | Daily high-low range % | 0 |
| hl_range_5d | max(H_{t-4:t}) / min(L_{t-4:t}) - 1 | 5-day high-low range | 5 |
| oc_range | |O_t - C_t| / C_t | Open-close range | 0 |
| volume_1d | V_t | Raw volume | 0 |
| volume_5d_avg | mean(V_{t-4:t}) | 5-day average volume | 5 |
| volume_ratio | V_t / mean(V_{t-19:t}) | Volume vs 20-day avg | 20 |

---

## 2. Technical Indicators

Standard technical indicators. All use past data only (no forward-looking).

### Moving Averages
| Feature | Formula | Lookback |
|---------|---------|----------|
| sma_5 | mean(C_{t-4:t}) | 5 |
| sma_10 | mean(C_{t-9:t}) | 10 |
| sma_20 | mean(C_{t-19:t}) | 20 |
| sma_50 | mean(C_{t-49:t}) | 50 |
| sma_200 | mean(C_{t-199:t}) | 200 |
| ema_5 | EMA(C, span=5) | 5 |
| ema_20 | EMA(C, span=20) | 20 |
| ema_50 | EMA(C, span=50) | 50 |

### Price vs MA Ratios
| Feature | Formula | Description |
|---------|---------|-------------|
| price_vs_sma_5 | C_t / sma_5 - 1 | Price relative to 5-day SMA |
| price_vs_sma_20 | C_t / sma_20 - 1 | Price relative to 20-day SMA |
| price_vs_sma_50 | C_t / sma_50 - 1 | Price relative to 50-day SMA |
| price_vs_ema_20 | C_t / ema_20 - 1 | Price relative to 20-day EMA |
| sma_5_vs_sma_20 | sma_5 / sma_20 - 1 | Short vs medium MA |
| sma_20_vs_sma_50 | sma_20 / sma_50 - 1 | Medium vs long MA |

### Oscillators
| Feature | Formula | Lookback |
|---------|---------|----------|
| rsi_14 | RSI(close, period=14) | 14 |
| rsi_7 | RSI(close, period=7) | 7 |
| stoch_k | Stochastic %K(14) | 14 |
| stoch_d | Stochastic %D(14) | 14 |

### MACD
| Feature | Formula | Description |
|---------|---------|-------------|
| macd_line | EMA(12) - EMA(26) | MACD line |
| macd_signal | EMA(macd_line, 9) | Signal line |
| macd_hist | macd_line - macd_signal | Histogram |
| macd_cross | 1 if macd_line > macd_signal else 0 | Crossover signal |

### Bollinger Bands
| Feature | Formula | Lookback |
|---------|---------|----------|
| bb_upper | SMA(20) + 2*STD(20) | 20 |
| bb_lower | SMA(20) - 2*STD(20) | 20 |
| bb_width | (bb_upper - bb_lower) / SMA(20) | 20 |
| bb_position | (C_t - bb_lower) / (bb_upper - bb_lower) | 20 |

### ATR (Average True Range)
| Feature | Formula | Lookback |
|---------|---------|----------|
| atr_14 | ATR(14) | 14 |
| atr_ratio | atr_14 / C_t | ATR as % of price |

### Rate of Change
| Feature | Formula | Lookback |
|---------|---------|----------|
| roc_5 | (C_t - C_{t-5}) / C_{t-5} | 5 |
| roc_10 | (C_t - C_{t-10}) / C_{t-10} | 10 |
| roc_20 | (C_t - C_{t-20}) / C_{t-20} | 20 |

### Volume Indicators
| Feature | Formula | Lookback |
|---------|---------|----------|
| obv | On-Balance Volume | All |
| obv_sma_20 | SMA(obv, 20) | 20 |
| volume_sma_20 | SMA(volume, 20) | 20 |
| volume_roc_5 | (V_t - V_{t-5}) / V_{t-5} | 5 |
| pv_trend | sign(return_1d) * volume_ratio | 1 |

---

## 3. Volatility Features

| Feature | Formula | Lookback |
|---------|---------|----------|
| vol_5d | std(log_return_{t-4:t}) * sqrt(252) | 5 |
| vol_10d | std(log_return_{t-9:t}) * sqrt(252) | 10 |
| vol_20d | std(log_return_{t-19:t}) * sqrt(252) | 20 |
| vol_60d | std(log_return_{t-59:t}) * sqrt(252) | 60 |
| vol_ratio_5_20 | vol_5d / vol_20d | Short vs long vol |
| vol_ratio_10_60 | vol_10d / vol_60d | Medium vs long vol |
| atr_14_norm | atr_14 / C_t | Normalized ATR |
| vol_regime | 1 if vol_20d > median(vol_20d, 252) else 0 | High/low vol regime |
| vol_change_5d | vol_5d / vol_5d.shift(5) - 1 | Volatility change |
| garch_forecast | GARCH(1,1) 1-step forecast | 60+ |

Note: GARCH features require sufficient history (min 100 observations). Use expanding window fit.

---

## 4. Market-Relative Features

Require index data (SPY, sector ETFs). Index close available same day, but use lagged for safety.

| Feature | Formula | Data Required | Lag |
|---------|---------|---------------|-----|
| beta_60d | cov(stock_ret, spy_ret) / var(spy_ret) | SPY returns | 1 |
| beta_252d | cov(stock_ret, spy_ret) / var(spy_ret) | SPY returns | 1 |
| rel_str_5d | stock_ret_5d - spy_ret_5d | SPY returns | 1 |
| rel_str_20d | stock_ret_20d - spy_ret_20d | SPY returns | 1 |
| rel_str_60d | stock_ret_60d - spy_ret_60d | SPY returns | 1 |
| sector_rel_5d | stock_ret_5d - sector_etf_ret_5d | Sector ETF | 1 |
| sector_rel_20d | stock_ret_20d - sector_etf_ret_20d | Sector ETF | 1 |
| corr_spy_20d | corr(stock_ret, spy_ret, 20) | SPY returns | 1 |
| corr_spy_60d | corr(stock_ret, spy_ret, 60) | SPY returns | 1 |
| alpha_60d | stock_ret_60d - beta_60d * spy_ret_60d | SPY returns | 1 |

Critical: Use index return from t-1 (previous close) when predicting at t close. Index close at t not known until after prediction.

---

## 5. Market Regime Features

Identify market state to condition predictions.

| Feature | Formula | Description |
|---------|---------|-------------|
| spy_trend_20d | SMA(SPY, 20) > SMA(SPY, 50) | SPY trend (bull/bear) |
| spy_trend_50d | SMA(SPY, 50) > SMA(SPY, 200) | Long-term trend |
| spy_vol_regime | SPY vol_20d > median(SPY vol_20d, 252) | Market vol regime |
| vix_level | VIX close | Fear gauge |
| vix_term_structure | VIX_30d / VIX_90d | Term structure |
| yield_curve | 10Y - 2Y Treasury | Recession indicator |
| dxy_trend | DXY > SMA(DXY, 50) | Dollar strength |
| hmm_state | HMM(SPY returns, n_states=3) | Hidden regime (bull/bear/sideways) |

HMM Training: Fit on expanding window, predict state for current day. State labels: 0=bear, 1=sideways, 2=bull.

---

## 6. Fundamental Features

CRITICAL: Fundamental data has reporting lag. Use minimum 60-day lag from period end.

| Feature | Source | Formula | Lag |
|---------|--------|---------|-----|
| eps_ttm | Income Statement | Trailing 12M EPS | 60d |
| eps_growth_qoq | Income Statement | (EPS_q - EPS_{q-1}) / |EPS_{q-1}| | 60d |
| eps_growth_yoy | Income Statement | (EPS_q - EPS_{q-4}) / |EPS_{q-4}| | 60d |
| revenue_ttm | Income Statement | Trailing 12M Revenue | 60d |
| revenue_growth_qoq | Income Statement | QoQ revenue growth | 60d |
| revenue_growth_yoy | Income Statement | YoY revenue growth | 60d |
| pe_ratio | Price / EPS_ttm | P/E ratio | 60d |
| pb_ratio | Price / Book Value | P/B ratio | 60d |
| ps_ratio | Price / Sales_ttm | P/S ratio | 60d |
| roe | Net Income / Equity | Return on Equity | 60d |
| roa | Net Income / Assets | Return on Assets | 60d |
| debt_to_equity | Total Debt / Equity | Leverage | 60d |
| current_ratio | Current Assets / Current Liabilities | Liquidity | 60d |
| gross_margin | Gross Profit / Revenue | Profitability | 60d |
| operating_margin | Operating Income / Revenue | Profitability | 60d |
| net_margin | Net Income / Revenue | Profitability | 60d |

Availability Rule: Fundamental for quarter Q available at earliest 60 days after quarter end. E.g., Q4 2023 (ends Dec 31) -> available ~Mar 1, use for predictions from ~May 1.

---

## 7. News/Sentiment Features

News collected from multiple sources. Sentiment via FinBERT or similar.

| Feature | Formula | Description | Lag |
|---------|---------|-------------|-----|
| news_count_1d | Count articles day t-1 | Volume | 1 |
| news_count_5d | Count articles t-5 to t-1 | Volume | 1 |
| news_count_20d | Count articles t-20 to t-1 | Volume | 1 |
| sentiment_mean_1d | Mean sentiment t-1 | Avg sentiment | 1 |
| sentiment_mean_5d | Mean sentiment t-5 to t-1 | Avg sentiment | 1 |
| sentiment_std_5d | Std sentiment t-5 to t-1 | Sentiment dispersion | 1 |
| positive_ratio_5d | Count(pos)/Total t-5 to t-1 | Bullishness | 1 |
| negative_ratio_5d | Count(neg)/Total t-5 to t-1 | Bearishness | 1 |
| news_recency | Hours since last article | Recency | 1 |
| source_credibility_weighted | Sum(sentiment * credibility) | Quality-weighted | 1 |

Sentiment Scale: -1 (very negative) to +1 (very positive), 0 = neutral.

Cutoff Rule: For prediction at market close (16:00 ET), only use news with timestamp < 16:00 ET same day. Conservative: use news up to t-1 (previous day).

---

## 8. Macro Features

| Feature | Source | Description | Lag |
|---------|--------|-------------|-----|
| vix_close | CBOE | VIX index level | 1 |
| vix_change_1d | VIX_t / VIX_{t-1} - 1 | VIX daily change | 1 |
| yield_10y | FRED | 10-year Treasury yield | 1 |
| yield_2y | FRED | 2-year Treasury yield | 1 |
| yield_curve | yield_10y - yield_2y | Term spread | 1 |
| dxy_close | FRED | Dollar index | 1 |
| oil_price | FRED/EIA | WTI crude price | 1 |
| gold_price | FRED | Gold price | 1 |

---

## Feature Availability Summary

| Feature Group | Available At Prediction Time | Requires External Data |
|---------------|------------------------------|------------------------|
| Price | Close of day T (16:00 ET) | No |
| Technical | Close of day T | No |
| Volatility | Close of day T | No |
| Market-Relative | Close of day T (with 1-day lag on index) | Yes (SPY, Sector ETFs) |
| Market Regime | Close of day T (with 1-day lag on macro) | Yes (VIX, Yields, DXY) |
| Fundamental | Close of day T (with 60-day lag) | Yes (Financial statements) |
| News/Sentiment | Close of day T (with 1-day lag) | Yes (News APIs) |
| Macro | Close of day T (with 1-day lag) | Yes (FRED, etc.) |

---

## Feature Computation Pipeline

`python
class FeaturePipeline:
    def __init__(self, feature_version: str, config: dict):
        self.version = feature_version
        self.config = config
        self.computers = {
            'price': PriceFeatureComputer(),
            'technical': TechnicalFeatureComputer(),
            'volatility': VolatilityFeatureComputer(),
            'market_relative': MarketRelativeFeatureComputer(),
            'regime': RegimeFeatureComputer(),
            'fundamental': FundamentalFeatureComputer(lag_days=60),
            'news': NewsFeatureComputer(lag_days=1),
            'macro': MacroFeatureComputer(lag_days=1),
        }
    
    def compute(self, prediction_date: pd.Timestamp, universe: List[str]) -> pd.DataFrame:
        CRITICAL: Only uses data with timestamp <= prediction_date
        features_list = []
        
        for group_name, computer in self.computers.items():
            group_features = computer.compute(prediction_date, universe)
            features_list.append(group_features)
        
        # Merge all feature groups on [symbol, prediction_date]
        all_features = features_list[0]
        for f in features_list[1:]:
            all_features = all_features.merge(f, on=['symbol', 'prediction_date'], how='outer')
        
        # Add metadata
        all_features['feature_version'] = self.version
        all_features['computed_at'] = pd.Timestamp.utcnow()
        
        return all_features
`

---

## Feature Selection & Filtering

### Correlation Filtering
- Remove features with |correlation| > 0.95 with another feature
- Keep the one with higher univariate predictive power

### Variance Filtering
- Remove features with near-zero variance (< 1e-6)
- Remove features constant for > 95% of samples

### Importance Filtering (Post-Training)
- Train baseline model (XGBoost)
- Remove features with importance < threshold (e.g., 0.001)
- Re-train and verify no performance degradation

### Stability Filtering (Walk-Forward)
- Compute feature importance per fold
- Remove features with inconsistent sign/rank across folds
- Target: Spearman correlation of importance ranks > 0.7 across folds

---

## Feature Store Schema

`sql
-- Offline feature store (Parquet partitioned by date)
CREATE TABLE features_offline (
    symbol VARCHAR(10),
    prediction_date DATE,
    feature_version VARCHAR(20),
    -- Price features (15)
    return_1d DOUBLE, return_5d DOUBLE, return_10d DOUBLE, return_20d DOUBLE,
    log_return_1d DOUBLE, log_return_5d DOUBLE,
    momentum_5d DOUBLE, momentum_20d DOUBLE,
    gap_up DOUBLE, gap_down DOUBLE,
    hl_range DOUBLE, hl_range_5d DOUBLE, oc_range DOUBLE,
    volume_1d BIGINT, volume_5d_avg DOUBLE, volume_ratio DOUBLE,
    -- Technical (25)
    sma_5 DOUBLE, sma_10 DOUBLE, sma_20 DOUBLE, sma_50 DOUBLE, sma_200 DOUBLE,
    ema_5 DOUBLE, ema_20 DOUBLE, ema_50 DOUBLE,
    price_vs_sma_5 DOUBLE, price_vs_sma_20 DOUBLE, price_vs_sma_50 DOUBLE,
    price_vs_ema_20 DOUBLE, sma_5_vs_sma_20 DOUBLE, sma_20_vs_sma_50 DOUBLE,
    rsi_14 DOUBLE, rsi_7 DOUBLE, stoch_k DOUBLE, stoch_d DOUBLE,
    macd_line DOUBLE, macd_signal DOUBLE, macd_hist DOUBLE, macd_cross INT,
    bb_upper DOUBLE, bb_lower DOUBLE, bb_width DOUBLE, bb_position DOUBLE,
    atr_14 DOUBLE, atr_ratio DOUBLE,
    roc_5 DOUBLE, roc_10 DOUBLE, roc_20 DOUBLE,
    obv BIGINT, obv_sma_20 DOUBLE, volume_sma_20 DOUBLE, volume_roc_5 DOUBLE, pv_trend DOUBLE,
    -- Volatility (10)
    vol_5d DOUBLE, vol_10d DOUBLE, vol_20d DOUBLE, vol_60d DOUBLE,
    vol_ratio_5_20 DOUBLE, vol_ratio_10_60 DOUBLE,
    atr_14_norm DOUBLE, vol_regime INT, vol_change_5d DOUBLE, garch_forecast DOUBLE,
    -- Market-Relative (10)
    beta_60d DOUBLE, beta_252d DOUBLE,
    rel_str_5d DOUBLE, rel_str_20d DOUBLE, rel_str_60d DOUBLE,
    sector_rel_5d DOUBLE, sector_rel_20d DOUBLE,
    corr_spy_20d DOUBLE, corr_spy_60d DOUBLE, alpha_60d DOUBLE,
    -- Regime (8)
    spy_trend_20d INT, spy_trend_50d INT, spy_vol_regime INT,
    vix_level DOUBLE, vix_term_structure DOUBLE,
    yield_curve DOUBLE, dxy_trend INT, hmm_state INT,
    -- Fundamental (15) - LAGGED 60 DAYS
    eps_ttm DOUBLE, eps_growth_qoq DOUBLE, eps_growth_yoy DOUBLE,
    revenue_ttm DOUBLE, revenue_growth_qoq DOUBLE, revenue_growth_yoy DOUBLE,
    pe_ratio DOUBLE, pb_ratio DOUBLE, ps_ratio DOUBLE,
    roe DOUBLE, roa DOUBLE, debt_to_equity DOUBLE,
    current_ratio DOUBLE, gross_margin DOUBLE, operating_margin DOUBLE, net_margin DOUBLE,
    -- News (10) - LAGGED 1 DAY
    news_count_1d INT, news_count_5d INT, news_count_20d INT,
    sentiment_mean_1d DOUBLE, sentiment_mean_5d DOUBLE, sentiment_std_5d DOUBLE,
    positive_ratio_5d DOUBLE, negative_ratio_5d DOUBLE,
    news_recency DOUBLE, source_credibility_weighted DOUBLE,
    -- Macro (8) - LAGGED 1 DAY
    vix_close DOUBLE, vix_change_1d DOUBLE,
    yield_10y DOUBLE, yield_2y DOUBLE, yield_curve DOUBLE,
    dxy_close DOUBLE, oil_price DOUBLE, gold_price DOUBLE,
    PRIMARY KEY (symbol, prediction_date, feature_version)
) PARTITIONED BY (prediction_date);
`

---

## Leakage Prevention in Feature Engineering

### Automated Checks (Run at Every Computation)

`python
def validate_features(features_df, prediction_date):
    errors = []
    
    # 1. No future dates in index
    if features_df['prediction_date'].max() > prediction_date:
        errors.append('Features contain future prediction_date')
    
    # 2. Fundamental lag check
    fund_cols = [c for c in features_df.columns if c in FUNDAMENTAL_COLUMNS]
    for col in fund_cols:
        # Verify data is lagged (implementation specific)
        pass
    
    # 3. News lag check
    news_cols = [c for c in features_df.columns if c.startswith('news_') or c.startswith('sentiment_')]
    for col in news_cols:
        # Verify lag enforced
        pass
    
    # 4. No target columns
    target_cols = [c for c in features_df.columns if 'target' in c.lower() or 'label' in c.lower()]
    if target_cols:
        errors.append(f'Target-like columns in features: {target_cols}')
    
    # 5. NaN check (warn, don't fail - tree models handle NaN)
    nan_pct = features_df.isnull().mean()
    high_nan = nan_pct[nan_pct > 0.5].index.tolist()
    if high_nan:
        warnings.warn(f'Features with >50% NaN: {high_nan}')
    
    if errors:
        raise LeakageError(errors)
`

---

## Feature Versioning

`
Feature Version Format: feat_v{MAJOR}.{MINOR}

MAJOR: Breaking change (add/remove feature groups, change formulas)
MINOR: Non-breaking (add individual features, fix bugs)

Examples:
- feat_v1.0: Initial release (price, technical, volatility)
- feat_v1.1: Added market-relative features
- feat_v1.2: Added regime features
- feat_v2.0: Added fundamental + news (major = new data sources)
- feat_v2.1: Fixed beta calculation bug
`

Version Hash: sha256(feature_code + config + dependency_versions)[:8]

Every training run records: dataset_version = f'{feature_version}_{label_version}_{split_hash}'

---

## Summary

- ~101 features across 8 groups
- Strict lag enforcement: Fundamentals (60d), News/Macro (1d), Market-relative (1d)
- No look-ahead: All features use data <= prediction_timestamp
- Versioned: Feature version pinned to model version
- Reproducible: Same computation code for training and inference
- Validated: Automated leakage checks at computation time