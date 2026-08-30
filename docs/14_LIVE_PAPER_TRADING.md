# 14_LIVE_PAPER_TRADING.md

## Live/Paper Trading Architecture

This document designs the live prediction and paper trading system.

## Architecture Overview

`mermaid
flowchart TD
    subgraph LiveData [Live Market Data]
        LD1[Real-time Quotes Polygon/Alpaca/IEX]
        LD2[Intraday Bars 1min, 5min, 15min]
        LD3[News Feed NewsAPI/RSS/Webhooks]
        LD4[Macro Data FRED/VIX/Yields]
    end
    
    subgraph FeatureGen [Feature Generation]
        FG1[Price Features]
        FG2[Technical Indicators]
        FG3[Volatility Features]
        FG4[Market-Relative]
        FG5[Regime Features]
        FG6[Fundamental (lagged)]
        FG7[News Sentiment (lagged)]
        FG8[Macro (lagged)]
    end
    
    subgraph Model [Model Inference]
        M1[Load Production Model]
        M2[Load Feature Version]
        M3[Compute Features]
        M4[Predict Probabilities]
        M5[Calibrate]
        M6[Confidence Score]
    end
    
    subgraph Risk [Risk Engine]
        R1[Position Limits]
        R2[Sector Limits]
        R3[Liquidity Check]
        R4[Model Uncertainty]
        R5[No-Trade Conditions]
    end
    
    subgraph Paper [Paper Trading Engine]
        PT1[Target Positions]
        PT2[Order Generation]
        PT3[Execution Simulation]
        PT4[P&L Calculation]
        PT5[Portfolio Tracking]
    end
    
    subgraph Logging [Prediction Logging]
        PL1[Prediction Record]
        PL2[Outcome Tracking]
        PL3[Performance Metrics]
    end
    
    subgraph Dashboard [Dashboard/API]
        D1[Live Predictions]
        D2[Paper Portfolio]
        D3[Performance]
        D4[Drift Alerts]
    end
    
    LD1 --> FG1
    LD2 --> FG1
    LD3 --> FG7
    LD4 --> FG8
    
    FG1 --> M3
    FG2 --> M3
    FG3 --> M3
    FG4 --> M3
    FG5 --> M3
    FG6 --> M3
    FG7 --> M3
    FG8 --> M3
    
    M1 --> M3
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
    
    M6 --> R1
    R1 --> R2
    R2 --> R3
    R3 --> R4
    R4 --> R5
    
    R5 --> PT1
    PT1 --> PT2
    PT2 --> PT3
    PT3 --> PT4
    PT4 --> PT5
    
    M6 --> PL1
    PT5 --> PL2
    PL1 --> PL3
    PL2 --> PL3
    
    PL3 --> D1
    PT5 --> D2
    PL3 --> D3
    PL3 --> D4
`

---

## Live Prediction Pipeline

### Scheduler
`python
class LivePredictionScheduler:
    def __init__(self, config):
        self.config = config
        self.prediction_times = config.prediction_times
        self.timezone = config.timezone
        self.is_running = False
    
    def start(self):
        self.is_running = True
        schedule.every().day.at('16:00').do(self.run_prediction_cycle)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)
    
    def run_prediction_cycle(self):
        prediction_time = pd.Timestamp.now(tz=self.timezone)
        
        if not self._is_trading_day(prediction_time):
            logger.info(f'Not a trading day: {prediction_time.date()}')
            return
        
        universe = self._get_universe(prediction_time)
        features = self.feature_pipeline.compute(prediction_time, universe)
        model = self.model_registry.load_production()
        predictions = self._generate_predictions(model, features, prediction_time)
        filtered = self.risk_engine.filter(predictions, prediction_time)
        self.prediction_logger.log(filtered)
        
        if self.config.paper_trading_enabled:
            self.paper_engine.process_predictions(filtered, prediction_time)
        
        self.dashboard.update(filtered)
        logger.info(f'Prediction cycle complete: {len(filtered)} predictions')
`

### Feature Computation at Prediction Time

CRITICAL: Only use data with timestamp less than or equal to prediction_time

For 16:00 ET prediction:
- Daily OHLCV: Use today's close (just printed)
- Intraday: Use up to 16:00
- Fundamentals: Lagged 60+ days
- News: Up to 15:59 ET (1-min buffer)
- Macro: Previous day's close

`python
def compute_live_features(prediction_time, universe):
    cutoff = prediction_time
    
    features = {}
    
    # Price/Technical/Volatility: Use daily data up to today
    daily_data = get_daily_data(universe, end_date=cutoff.date())
    features['price'] = compute_price_features(daily_data)
    features['technical'] = compute_technical_features(daily_data)
    features['volatility'] = compute_volatility_features(daily_data)
    
    # Market-relative: Need index data (use previous close for safety)
    index_data = get_index_data(['SPY', 'QQQ', 'IWM'], end_date=cutoff.date() - 1)
    features['market_relative'] = compute_market_relative(daily_data, index_data)
    
    # Regime: Use macro data up to previous day
    macro_data = get_macro_data(end_date=cutoff.date() - 1)
    features['regime'] = compute_regime_features(daily_data, macro_data)
    
    # Fundamentals: Lagged 60 days
    fund_data = get_fundamentals(universe, as_of=cutoff.date() - pd.Timedelta(days=60))
    features['fundamental'] = compute_fundamental_features(fund_data)
    
    # News: Up to 1 min before prediction
    news_cutoff = cutoff - pd.Timedelta(minutes=1)
    news_data = get_news(universe, end_date=news_cutoff)
    features['news'] = compute_news_features(news_data)
    
    # Macro: Previous day
    macro_data = get_macro_data(end_date=cutoff.date() - 1)
    features['macro'] = compute_macro_features(macro_data)
    
    # Merge all
    all_features = merge_features(features, on=['symbol', 'prediction_date'])
    all_features['prediction_date'] = cutoff.date()
    
    return all_features
`

---

## Paper Trading Engine

### Order Execution Simulation
`python
class PaperTradingEngine:
    def __init__(self, config, initial_capital=1_000_000):
        self.config = config
        self.portfolio = PaperPortfolio(initial_capital)
        self.orders = []
        self.trades = []
        self.daily_snapshots = []
    
    def process_predictions(self, predictions, prediction_time):
        ranked = self._rank_predictions(predictions)
        targets = self._calculate_targets(ranked, prediction_time)
        orders = self._generate_orders(targets, prediction_time)
        
        for order in orders:
            self._execute_order(order, prediction_time)
        
        self._mark_to_market(prediction_time)
        self._record_snapshot(prediction_time)
    
    def _execute_order(self, order, prediction_time):
        execution_date = self._get_next_trading_day(prediction_time)
        execution_price = self._get_execution_price(order.symbol, execution_date, order.side)
        
        slippage = self._calculate_slippage(order, execution_price)
        filled_price = execution_price * (1 + slippage * (1 if order.side == 'buy' else -1))
        
        trade_value = filled_price * order.shares
        commission = self._calculate_commission(trade_value, order.shares)
        spread_cost = self._calculate_spread_cost(trade_value)
        total_cost = commission + spread_cost
        
        if order.side == 'buy':
            self.portfolio.buy(order.symbol, order.shares, filled_price, total_cost)
        else:
            self.portfolio.sell(order.symbol, order.shares, filled_price, total_cost)
        
        trade = Trade(
            trade_id=uuid.uuid4().hex[:12],
            symbol=order.symbol,
            entry_date=execution_date,
            side=order.side,
            entry_price=filled_price,
            shares=order.shares,
            commission=commission,
            spread_cost=spread_cost,
            slippage=slippage,
            total_cost=total_cost,
            prediction_id=order.prediction_id,
            model_version=order.model_version,
        )
        self.trades.append(trade)
`

### Portfolio Management
`python
class PaperPortfolio:
    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.closed_trades = []
    
    def buy(self, symbol, shares, price, cost):
        value = shares * price + cost
        if value > self.cash:
            raise ValueError('Insufficient cash')
        
        self.cash -= value
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.shares += shares
            pos.cost_basis = ((pos.shares - shares) * pos.cost_basis + shares * price) / pos.shares
        else:
            self.positions[symbol] = Position(symbol, shares, price)
    
    def sell(self, symbol, shares, price, cost):
        if symbol not in self.positions:
            raise ValueError(f'No position in {symbol}')
        
        pos = self.positions[symbol]
        if shares > pos.shares:
            raise ValueError('Cannot sell more than position')
        
        proceeds = shares * price - cost
        self.cash += proceeds
        
        pnl = shares * (price - pos.cost_basis) - cost
        self.closed_trades.append({
            'symbol': symbol,
            'shares': shares,
            'entry_price': pos.cost_basis,
            'exit_price': price,
            'pnl': pnl,
            'cost': cost,
        })
        
        pos.shares -= shares
        if pos.shares == 0:
            del self.positions[symbol]
    
    def mark_to_market(self, prices):
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.current_price = prices[symbol]
                pos.market_value = pos.shares * pos.current_price
                pos.unrealized_pnl = pos.shares * (pos.current_price - pos.cost_basis)
    
    @property
    def total_value(self):
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
`

---

## Prediction Logging (Audit Trail)

### Immutable Prediction Log
`python
@dataclass
class PredictionLog:
    prediction_id: str
    symbol: str
    prediction_timestamp: pd.Timestamp
    model_version: str
    feature_version: str
    feature_hash: str
    horizon_days: int
    p_up: float
    p_down: float
    p_sideways: float
    confidence: float
    expected_return: float
    predicted_class: int
    regime: int
    volatility_regime: int
    rank_up: int
    rank_expected_return: int
    risk_score: float
    position_size_pct: float
    no_trade_reason: Optional[str] = None
    outcome_timestamp: Optional[pd.Timestamp] = None
    actual_return: Optional[float] = None
    actual_class: Optional[int] = None
    correct: Optional[bool] = None
    pnl: Optional[float] = None
    
    def to_dict(self):
        return asdict(self)
`

### Outcome Resolution
`python
class OutcomeResolver:
    def __init__(self, price_data_source):
        self.price_data = price_data_source
    
    def resolve_outcomes(self, horizon_days=5):
        unresolved = self.prediction_logger.get_unresolved()
        
        for pred in unresolved:
            outcome_date = pred.prediction_timestamp + pd.Timedelta(days=horizon_days)
            outcome_date = self._next_trading_day(outcome_date)
            
            if outcome_date <= pd.Timestamp.now(tz='UTC'):
                entry_price = self.price_data.get_close(pred.symbol, pred.prediction_timestamp.date())
                exit_price = self.price_data.get_close(pred.symbol, outcome_date.date())
                
                if entry_price and exit_price:
                    actual_return = exit_price / entry_price - 1
                    
                    if actual_return > 0.02:
                        actual_class = 2
                    elif actual_return < -0.02:
                        actual_class = 0
                    else:
                        actual_class = 1
                    
                    self.prediction_logger.update_outcome(
                        pred.prediction_id,
                        outcome_timestamp=outcome_date,
                        actual_return=actual_return,
                        actual_class=actual_class,
                        correct=(pred.predicted_class == actual_class),
                        pnl=actual_return * pred.position_size_pct
                    )
`

---

## Performance Tracking

### Real-Time Metrics
`python
class PerformanceTracker:
    def __init__(self, prediction_logger):
        self.logger = prediction_logger
    
    def compute_metrics(self, window_days=30):
        preds = self.logger.get_predictions(
            start_date=pd.Timestamp.now() - pd.Timedelta(days=window_days)
        )
        resolved = preds.dropna(subset=['actual_class'])
        
        if len(resolved) == 0:
            return {}
        
        y_true = resolved['actual_class'].values
        y_pred = resolved['predicted_class'].values
        y_prob = resolved[['p_up', 'p_down', 'p_sideways']].values
        
        return {
            'window_days': window_days,
            'n_predictions': len(resolved),
            'n_total': len(preds),
            'resolution_rate': len(resolved) / len(preds),
            'accuracy': accuracy_score(y_true, y_pred),
            'log_loss': log_loss(y_true, y_prob),
            'brier': brier_score(y_true, y_prob),
            'ece': expected_calibration_error(y_true, y_prob),
            'roc_auc': roc_auc_score(y_true, y_prob, multi_class='ovr'),
            'total_pnl': resolved['pnl'].sum(),
            'avg_pnl': resolved['pnl'].mean(),
            'sharpe': self._compute_sharpe(resolved),
            'win_rate': (resolved['pnl'] > 0).mean(),
            'profit_factor': resolved[resolved['pnl'] > 0]['pnl'].sum() / abs(resolved[resolved['pnl'] < 0]['pnl'].sum()),
        }
`

---

## Divergence Detection (Backtest vs Live)

`python
def detect_divergence(backtest_metrics, live_metrics, threshold=0.5):
    alerts = []
    
    for metric in ['log_loss', 'accuracy', 'sharpe', 'win_rate']:
        if metric in backtest_metrics and metric in live_metrics:
            expected = backtest_metrics[metric]
            actual = live_metrics[metric]
            std = backtest_metrics.get(f'{metric}_std', 0.01)
            
            z_score = (actual - expected) / std if std > 0 else 0
            
            if abs(z_score) > threshold:
                alerts.append({
                    'metric': metric,
                    'expected': expected,
                    'actual': actual,
                    'z_score': z_score,
                    'severity': 'HIGH' if abs(z_score) > 2 else 'MEDIUM'
                })
    
    return alerts
`

---

## Live vs Paper vs Production

| Aspect | Live Prediction | Paper Trading | Production |
|--------|----------------|---------------|------------|
| Data | Real-time | Real-time | Real-time |
| Model | Production | Production | Production |
| Execution | None | Simulated | Real broker |
| P&L | Theoretical | Simulated | Real |
| Risk | None | Simulated | Real |
| Logging | Full | Full | Full |
| Regulatory | No | No | Yes |

---

## Deployment Checklist

Before enabling paper trading:
- [ ] Model passes walk-forward validation
- [ ] Calibration ECE < 0.05 on test
- [ ] Backtest Sharpe > 1.0 net of costs
- [ ] Feature pipeline produces identical results offline/online
- [ ] Prediction logging immutable and complete
- [ ] Paper trading engine tested with historical data
- [ ] Risk limits configured and tested
- [ ] Alerting on divergence configured
- [ ] Dashboard shows live predictions and paper P&L
- [ ] Rollback procedure documented

---

## Summary

| Component | Implementation |
|-----------|----------------|
| Scheduler | APScheduler/Cron at 16:00 ET |
| Features | Same pipeline as training (feature store) |
| Model | Loaded from MLflow registry (pinned version) |
| Calibration | Isotonic (fitted on calibration set) |
| Risk | Hard limits (position, sector, drawdown) |
| Paper Execution | Next-day open + slippage + costs |
| Logging | Immutable, append-only, pre-outcome |
| Monitoring | Rolling metrics, divergence alerts |
| Dashboard | Real-time predictions + paper portfolio |