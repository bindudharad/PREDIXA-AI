# DATA_DICTIONARY.md

## Data Dictionary - All Dataset Columns and Meanings

## Raw OHLCV (prices table)

| Column | Type | Description |
|--------|------|-------------|
| symbol | VARCHAR(10) | Stock ticker symbol |
| date | DATE | Trading date |
| open | DECIMAL(10,4) | Opening price |
| high | DECIMAL(10,4) | High price |
| low | DECIMAL(10,4) | Low price |
| close | DECIMAL(10,4) | Closing price |
| adj_close | DECIMAL(10,4) | Split/dividend adjusted close |
| volume | BIGINT | Trading volume |
| dividend | DECIMAL(10,4) | Dividend amount (if ex-date) |
| split_factor | DECIMAL(10,6) | Split factor (e.g., 2.0 for 2:1) |

## Corporate Actions

| Column | Type | Description |
|--------|------|-------------|
| action_id | SERIAL | Unique action identifier |
| symbol | VARCHAR(10) | Stock ticker |
| ex_date | DATE | Ex-date of action |
| announced_date | DATE | Announcement date |
| action_type | VARCHAR(20) | SPLIT, DIVIDEND, MERGER, SPINOFF |
| ratio | DECIMAL(10,6) | Split ratio |
| amount | DECIMAL(10,4) | Dividend amount |
| details | JSONB | Additional details |

## Fundamentals

| Column | Type | Description |
|--------|------|-------------|
| symbol | VARCHAR(10) | Stock ticker |
| period_end | DATE | Fiscal period end date |
| reported_date | DATE | Date reported to SEC |
| revenue | BIGINT | Total revenue |
| net_income | BIGINT | Net income |
| eps | DECIMAL(10,4) | Earnings per share (diluted) |
| book_value | BIGINT | Total equity |
| total_debt | BIGINT | Total debt |
| total_equity | BIGINT | Total equity |
| current_assets | BIGINT | Current assets |
| current_liabilities | BIGINT | Current liabilities |
| gross_profit | BIGINT | Gross profit |
| operating_income | BIGINT | Operating income |

## Features (features table - JSONB feature_values)

### Price Features
- return_1d, return_5d, return_10d, return_20d: Simple returns over N days
- log_return_1d, log_return_5d: Log returns
- momentum_5d, momentum_20d: Price momentum
- gap_up, gap_down: Overnight gap up/down %
- hl_range: Daily high-low range %
- hl_range_5d: 5-day high-low range %
- oc_range: Open-close range %
- volume_1d: Daily volume
- volume_5d_avg: 5-day average volume
- volume_ratio: Volume vs 20-day average

### Technical Features
- sma_5, sma_10, sma_20, sma_50, sma_200: Simple moving averages
- ema_5, ema_20, ema_50: Exponential moving averages
- price_vs_sma_5, price_vs_sma_20, price_vs_sma_50: Price vs MA ratios
- price_vs_ema_20: Price vs EMA ratio
- sma_5_vs_sma_20, sma_20_vs_sma_50: MA crossover signals
- rsi_14, rsi_7: RSI (14, 7 periods)
- stoch_k, stoch_d: Stochastic oscillator
- macd_line, macd_signal, macd_hist, macd_cross: MACD
- bb_upper, bb_lower, bb_width, bb_position: Bollinger Bands
- atr_14, atr_ratio: Average True Range
- roc_5, roc_10, roc_20: Rate of Change
- obv, obv_sma_20: On-Balance Volume
- volume_sma_20, volume_roc_5, pv_trend: Volume indicators

### Volatility Features
- vol_5d, vol_10d, vol_20d, vol_60d: Annualized rolling volatility
- vol_ratio_5_20, vol_ratio_10_60: Volatility ratios
- atr_14_norm: Normalized ATR
- vol_regime: High/low volatility regime (binary)
- vol_change_5d: 5-day volatility change
- garch_forecast: GARCH(1,1) 1-step forecast

### Market-Relative Features
- beta_60d, beta_252d: Beta vs SPY
- rel_str_5d, rel_str_20d, rel_str_60d: Relative strength vs SPY
- sector_rel_5d, sector_rel_20d: Relative strength vs sector ETF
- corr_spy_20d, corr_spy_60d: Correlation with SPY
- alpha_60d: Jensen's alpha vs SPY

### Regime Features
- spy_trend_20d, spy_trend_50d: SPY trend (bull/bear)
- spy_vol_regime: SPY volatility regime
- vix_level: VIX index level
- vix_term_structure: VIX 30d/90d ratio
- yield_curve: 10Y - 2Y Treasury spread
- dxy_trend: DXY trend
- hmm_state: HMM regime state (0=bear, 1=sideways, 2=bull)

### Fundamental Features (60-day lag)
- eps_ttm: Trailing 12M EPS
- eps_growth_qoq, eps_growth_yoy: EPS growth
- revenue_ttm: Trailing 12M revenue
- revenue_growth_qoq, revenue_growth_yoy: Revenue growth
- pe_ratio, pb_ratio, ps_ratio: Valuation ratios
- roe, roa: Return on equity/assets
- debt_to_equity: Leverage
- current_ratio: Liquidity
- gross_margin, operating_margin, net_margin: Profitability

### News Features (1-day lag)
- news_count_1d, news_count_5d, news_count_20d: Article counts
- sentiment_mean_1d, sentiment_mean_5d: Average sentiment
- sentiment_std_5d: Sentiment dispersion
- positive_ratio_5d, negative_ratio_5d: Sentiment ratios
- news_recency: Hours since last article
- source_credibility_weighted: Credibility-weighted sentiment

### Macro Features (1-day lag)
- vix_close, vix_change_1d: VIX level and change
- yield_10y, yield_2y: Treasury yields
- yield_curve: 10Y-2Y spread
- dxy_close: Dollar index
- oil_price, gold_price: Commodity prices

## Labels (labels table)

| Column | Type | Description |
|--------|------|-------------|
| symbol | VARCHAR(10) | Stock ticker |
| prediction_date | DATE | Date prediction is for |
| label_version | VARCHAR(20) | Label generation version |
| label_3class | SMALLINT | 0=DOWN, 1=SIDEWAYS, 2=UP |
| label_2class | SMALLINT | 0=NOT_PROFITABLE, 1=PROFITABLE |
| future_return | DECIMAL(10,6) | Forward return (close-to-close) |

## Predictions (predictions table)

| Column | Type | Description |
|--------|------|-------------|
| prediction_id | VARCHAR(50) | Unique prediction ID |
| symbol | VARCHAR(10) | Stock ticker |
| prediction_timestamp | TIMESTAMP | When prediction made |
| model_id | VARCHAR(50) | Model version used |
| feature_version | VARCHAR(20) | Feature version used |
| horizon_days | SMALLINT | Prediction horizon |
| p_up | DECIMAL(6,4) | Probability UP |
| p_down | DECIMAL(6,4) | Probability DOWN |
| p_sideways | DECIMAL(6,4) | Probability SIDEWAYS |
| confidence | DECIMAL(6,4) | Confidence score |
| expected_return | DECIMAL(10,6) | Probability-weighted expected return |
| predicted_class | SMALLINT | Predicted class (0,1,2) |
| feature_hash | VARCHAR(64) | Hash of feature vector |
| regime | SMALLINT | Market regime at prediction |
| vol_regime | SMALLINT | Volatility regime |
| rank_up | INTEGER | Rank by P(UP) |
| rank_expected_return | INTEGER | Rank by expected return |
| risk_score | DECIMAL(6,4) | Risk score |
| position_size_pct | DECIMAL(6,4) | Recommended position size |
| no_trade_reason | VARCHAR(255) | Reason if no trade |

## Outcomes (outcomes table)

| Column | Type | Description |
|--------|------|-------------|
| prediction_id | VARCHAR(50) | Links to predictions |
| outcome_timestamp | TIMESTAMP | When outcome known |
| actual_return | DECIMAL(10,6) | Realized return |
| actual_class | SMALLINT | Realized class |
| correct | BOOLEAN | Prediction correct? |
| pnl | DECIMAL(10,6) | P&L if traded |

## Paper Trades (paper_trades table)

| Column | Type | Description |
|--------|------|-------------|
| trade_id | VARCHAR(50) | Unique trade ID |
| symbol | VARCHAR(10) | Stock ticker |
| entry_date | TIMESTAMP | Entry timestamp |
| exit_date | TIMESTAMP | Exit timestamp |
| side | VARCHAR(10) | BUY/SELL |
| entry_price | DECIMAL(10,4) | Entry price |
| exit_price | DECIMAL(10,4) | Exit price |
| shares | INTEGER | Number of shares |
| pnl | DECIMAL(12,2) | Profit/loss |
| commission | DECIMAL(10,2) | Commission paid |
| spread_cost | DECIMAL(10,2) | Spread cost |
| slippage | DECIMAL(10,2) | Slippage cost |
| total_cost | DECIMAL(10,2) | Total transaction cost |
| prediction_id | VARCHAR(50) | Source prediction |
| model_id | VARCHAR(50) | Model version |
| status | VARCHAR(20) | OPEN/CLOSED |

## Market Regimes (market_regimes table)

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Date |
| hmm_state | SMALLINT | HMM state (0=bear, 1=sideways, 2=bull) |
| vol_regime | SMALLINT | Volatility regime (0=low, 1=high) |
| vix | DECIMAL(6,2) | VIX level |
| yield_curve | DECIMAL(6,2) | 10Y-2Y spread |
| trend | VARCHAR(20) | Trend label |
| spy_above_sma20 | BOOLEAN | SPY > SMA(20) |
| spy_above_sma50 | BOOLEAN | SPY > SMA(50) |
| spy_above_sma200 | BOOLEAN | SPY > SMA(200) |

## Portfolio (portfolio table - daily snapshots)

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Snapshot date |
| cash | DECIMAL(15,2) | Cash balance |
| positions_value | DECIMAL(15,2) | Positions market value |
| total_value | DECIMAL(15,2) | Total portfolio value |
| daily_pnl | DECIMAL(15,2) | Daily P&L |
| daily_return | DECIMAL(10,6) | Daily return |
| positions | JSONB | Position details |
| gross_exposure | DECIMAL(10,4) | Gross exposure |
| net_exposure | DECIMAL(10,4) | Net exposure |
| n_positions | SMALLINT | Number of positions |
| max_drawdown | DECIMAL(6,4) | Max drawdown to date |
| current_drawdown | DECIMAL(6,4) | Current drawdown |
