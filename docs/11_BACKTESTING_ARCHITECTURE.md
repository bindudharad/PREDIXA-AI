# 11_BACKTESTING_ARCHITECTURE.md

## Backtesting Architecture

This document designs a realistic backtesting framework that separates prediction performance from trading performance.

## Core Principle

> Backtesting must simulate reality as closely as possible. Every simplification introduces optimism bias.

## Backtesting vs Prediction Evaluation

`mermaid
flowchart LR
    subgraph PredEval [Prediction Evaluation]
        PE1[Classification Metrics Accuracy, F1, AUC]
        PE2[Probabilistic Metrics Log Loss, Brier, ECE]
        PE3[Calibration Reliability Diagrams]
    end
    
    subgraph Backtest [Backtesting / Trading Simulation]
        BT1[Entry/Exit Rules]
        BT2[Position Sizing]
        BT3[Transaction Costs]
        BT4[Slippage/Spread]
        BT5[Portfolio Constraints]
        BT6[P&L Calculation]
        BT7[Risk Metrics Sharpe, Drawdown]
    end
    
    PE1 --> BT1
    PE2 --> BT1
    PE3 --> BT1
`

Key Distinction:
- Prediction evaluation: How well do probabilities match outcomes?
- Backtesting: How much money would this strategy make/lose?

---

## Backtest Engine Design

### Event-Driven Architecture (Not Vectorized)

`python
class BacktestEngine:
    def __init__(self, config):
        self.config = config
        self.portfolio = Portfolio(config.initial_capital)
        self.orders = []
        self.trades = []
        self.daily_snapshots = []
    
    def run(self, predictions, price_data):
        # Event-driven simulation
        # For each prediction date:
        # 1. Get predictions for that date
        # 2. Apply risk filters
        # 3. Generate target positions
        # 4. Execute orders at next available price
        # 5. Update portfolio
        # 6. Record everything
        predictions = predictions.sort_values('prediction_date')
        price_data = price_data.sort_values(['symbol', 'date'])
        
        for pred_date in predictions['prediction_date'].unique():
            self._process_date(pred_date, predictions, price_data)
        
        return self._generate_results()
    
    def _process_date(self, pred_date, predictions, price_data):
        # 1. Get predictions for this date
        day_preds = predictions[predictions['prediction_date'] == pred_date]
        
        # 2. Apply ranking and filters
        ranked = self._rank_and_filter(day_preds)
        
        # 3. Calculate target positions
        targets = self._calculate_target_positions(ranked, pred_date, price_data)
        
        # 4. Generate orders to reach targets
        orders = self._generate_orders(targets, pred_date, price_data)
        
        # 5. Execute orders
        for order in orders:
            self._execute_order(order, price_data)
        
        # 6. Mark-to-market
        self._mark_to_market(pred_date, price_data)
        
        # 7. Record snapshot
        self._record_snapshot(pred_date)
`

---

## Entry and Exit Rules

### Entry Rules
| Rule | Description | Price Used |
|------|-------------|------------|
| Close-to-Close | Enter at close of prediction day | Close(T) |
| Next Open | Enter at next day open | Open(T+1) |
| Next VWAP | Enter at next day VWAP | VWAP(T+1) |
| Limit Order | Enter at limit price (simulate fill rate) | Limit |

Default v1: Next Open (most realistic for daily predictions made at close)

### Exit Rules
| Rule | Description |
|------|-------------|
| Fixed Horizon | Exit at close of T+horizon |
| Stop Loss | Exit if price moves against by X% |
| Take Profit | Exit if price moves in favor by X% |
| Trailing Stop | Trail stop at X% from peak |
| Time Stop | Exit after max holding period |

Default v1: Fixed Horizon (matches prediction horizon)

---

## Transaction Cost Model

### Cost Components
`python
@dataclass
class TransactionCosts:
    commission_per_share: float = 0.005
    commission_min: float = 1.0
    commission_max_pct: float = 0.005
    spread_bps: float = 10
    slippage_bps: float = 5
    slippage_model: str = 'square_root'
    borrow_fee_bps_per_day: float = 50
    short_term_tax_rate: float = 0.37
    long_term_tax_rate: float = 0.20
`

### Cost Calculation
`python
def calculate_trade_cost(trade_value, shares, side, costs):
    commission = max(costs.commission_min, 
                    min(costs.commission_per_share * shares,
                        costs.commission_max_pct * trade_value))
    spread_cost = costs.spread_bps / 10000 * trade_value
    
    if costs.slippage_model == 'square_root':
        adv = 1_000_000
        participation = shares / adv
        slippage = costs.slippage_bps / 10000 * np.sqrt(participation) * trade_value
    elif costs.slippage_model == 'linear':
        slippage = costs.slippage_bps / 10000 * trade_value
    else:
        slippage = 0
    
    total = commission + spread_cost + slippage
    return total
`

### Realistic Default Costs (v1)
| Component | Value | Source |
|-----------|-------|--------|
| Commission | .005/share, min  | IBKR Pro |
| Spread | 10 bps (0.10%) | Large cap typical |
| Slippage | 5 bps (square-root) | Conservative |
| Total Round-Trip | ~30-40 bps | Per trade |

---

## Position Sizing

### Methods
`python
def calculate_position_size(signal_strength, portfolio_value, config):
    if config.method == 'fixed_fractional':
        base_size = config.max_position_pct * portfolio_value
        return base_size * signal_strength
    
    elif config.method == 'volatility_targeted':
        target_vol = config.target_volatility
        asset_vol = config.asset_volatility
        base_size = (target_vol / asset_vol) * portfolio_value
        return min(base_size * signal_strength, config.max_position_pct * portfolio_value)
    
    elif config.method == 'kelly':
        win_rate = config.kelly_win_rate
        win_loss_ratio = config.kelly_win_loss_ratio
        kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
        kelly_fraction = max(0, min(kelly_fraction, config.kelly_max))
        return kelly_fraction * portfolio_value * signal_strength
    
    elif config.method == 'risk_parity':
        return portfolio_value / config.n_positions * signal_strength
`

### Portfolio Constraints
`python
@dataclass
class PortfolioConstraints:
    max_position_pct: float = 0.10
    max_sector_pct: float = 0.30
    max_single_side_pct: float = 0.70
    max_gross_exposure: float = 1.50
    max_net_exposure: float = 1.00
    max_turnover_monthly: float = 2.0
    max_drawdown_pct: float = 0.20
    min_cash_pct: float = 0.05
`

---

## Slippage and Market Impact Models

### Square-Root Model (Almgren-Chriss Simplified)
`python
def square_root_slippage(shares, adv, volatility, spread_bps):
    participation = shares / adv
    if participation <= 0:
        return 0
    temp_impact = volatility * np.sqrt(participation) * 10000
    spread_cost = spread_bps / 2
    return temp_impact + spread_cost
`

---

## Backtest Outputs

### Trade Log
`python
@dataclass
class Trade:
    trade_id: str
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    side: str
    entry_price: float
    exit_price: float
    shares: int
    entry_value: float
    exit_value: float
    pnl: float
    pnl_pct: float
    commission: float
    spread_cost: float
    slippage: float
    total_cost: float
    holding_days: int
    prediction_prob_up: float
    prediction_prob_down: float
    prediction_confidence: float
    model_version: str
`

### Portfolio Time Series
`python
@dataclass
class PortfolioSnapshot:
    date: pd.Timestamp
    cash: float
    positions_value: float
    total_value: float
    daily_pnl: float
    daily_return: float
    gross_exposure: float
    net_exposure: float
    n_positions: int
    max_drawdown: float
    current_drawdown: float
`

### Summary Metrics
`python
@dataclass
class BacktestResult:
    total_return: float
    annualized_return: float
    total_return_net: float
    annualized_return_net: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    volatility_annual: float
    downside_volatility: float
    n_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    avg_holding_days: float
    turnover_annual: float
    total_commission: float
    total_spread: float
    total_slippage: float
    total_costs: float
    cost_drag_bps: float
    avg_prediction_confidence: float
    prediction_accuracy: float
    equity_curve: pd.Series
    daily_returns: pd.Series
    drawdown_series: pd.Series
    trade_log: List[Trade]
`

---

## Separating Prediction vs Trading Performance

`mermaid
flowchart TD
    A[Model Predictions Probabilities] --> B[Ranking Engine Top-K Selection]
    B --> C[Risk Engine Position Sizing Constraints]
    C --> D[Execution Simulator Costs, Slippage]
    D --> E[Portfolio P&L]
    
    A --> F[Prediction Metrics Accuracy, LogLoss, Brier, ECE]
    E --> G[Trading Metrics Sharpe, Drawdown, Returns]
    
    F -.->|Diagnostic| G
    G -.->|Feedback| A
`

### Why Separate?
1. Good predictions != Good trading: High accuracy on SIDEWAYS class does not help trading
2. Costs matter: 55% accuracy with 30bps costs loses money
3. Sizing matters: Kelly vs fixed fractional can flip Sharpe sign
4. Risk management: Stop losses, position limits change everything

### Reporting Both
Always report:
- Prediction metrics (log-loss, Brier, ECE, accuracy per class)
- Trading metrics (Sharpe, Sortino, max DD, net return)
- Attribution: How much of trading P&L comes from prediction vs sizing vs risk management

---

## Backtest Validation (No Overfitting)

### Walk-Forward Backtest
`python
def walkforward_backtest(predictions, prices, config, n_folds=5):
    results = []
    
    for fold_idx, (train_dates, val_dates, test_dates) in enumerate(walkforward_splits):
        test_preds = predictions[predictions['prediction_date'].isin(test_dates)]
        test_prices = prices[prices['date'].isin(test_dates + [test_dates[-1] + horizon])]
        
        engine = BacktestEngine(config)
        result = engine.run(test_preds, test_prices)
        
        results.append({
            'fold': fold_idx,
            'test_period': (test_dates[0], test_dates[-1]),
            'result': result
        })
    
    return results
`

### Out-of-Sample Only
- NEVER optimize backtest parameters on full history
- Parameters (costs, sizing, constraints) set BEFORE seeing any backtest results
- Only exception: Parameter sensitivity analysis (report all, do not cherry-pick)

---

## Common Backtest Pitfalls (Avoid These)

| Pitfall | Why Wrong | Fix |
|---------|-----------|-----|
| Vectorized backtest | Ignores path-dependency, order flow | Use event-driven |
| No transaction costs | Gross returns meaningless | Always include costs |
| Perfect fills | Real markets have slippage | Model slippage |
| Unlimited leverage | Margin calls, risk | Enforce constraints |
| Survivorship bias | Only tests on winners | Include delisted |
| Look-ahead in signals | Using future data | Strict temporal |
| No out-of-sample | Overfit to history | Walk-forward |
| Single period | Luck vs skill | Multiple folds |
| Ignoring borrow costs | Shorts expensive | Include borrow fees |
| No tax modeling | Taxes significant | Model if applicable |

---

## Backtest Configuration (v1 Defaults)

`python
DEFAULT_BACKTEST_CONFIG = BacktestConfig(
    initial_capital=1_000_000,
    entry_rule='next_open',
    exit_rule='fixed_horizon',
    costs=TransactionCosts(
        commission_per_share=0.005,
        commission_min=1.0,
        spread_bps=10,
        slippage_bps=5,
        slippage_model='square_root',
    ),
    sizing=PositionSizingConfig(
        method='fixed_fractional',
        max_position_pct=0.05,
    ),
    constraints=PortfolioConstraints(
        max_position_pct=0.10,
        max_sector_pct=0.30,
        max_gross_exposure=1.0,
        max_turnover_monthly=2.0,
    ),
    universe='sp500_liquid',
    min_price=5.0,
    min_avg_volume=500_000,
)
`

---

## Summary

| Component | Decision |
|-----------|----------|
| Engine Type | Event-driven (not vectorized) |
| Entry | Next-day open |
| Exit | Fixed horizon (matches prediction) |
| Costs | Commission + Spread + Square-root slippage |
| Sizing | Fixed fractional (5% max) |
| Constraints | Position, sector, gross, turnover limits |
| Validation | Walk-forward only |
| Reporting | Both prediction AND trading metrics |

Remember: A backtest is a simulation, not reality. The only validation that matters is live paper trading.