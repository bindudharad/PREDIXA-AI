# 19_DATABASE_DESIGN.md

## Database Design

This document defines the database schema for the PREDIXA AI system.

## ER Diagram

`mermaid
erDiagram
    STOCKS ||--o{ PRICES : has
    STOCKS ||--o{ FUNDAMENTALS : has
    STOCKS ||--o{ CORPORATE_ACTIONS : has
    STOCKS ||--o{ PREDICTIONS : generates
    STOCKS ||--o{ PAPER_TRADES : trades
    
    MODELS ||--o{ PREDICTIONS : produces
    MODELS ||--o{ EXPERIMENTS : trained_in
    MODELS ||--o{ BACKTESTS : evaluated_in
    
    EXPERIMENTS ||--o{ MODELS : produces
    EXPERIMENTS ||--o{ DATASETS : uses
    
    DATASETS ||--o{ FEATURES : contains
    DATASETS ||--o{ LABELS : contains
    
    PREDICTIONS ||--o{ OUTCOMES : resolves_to
    PAPER_TRADES ||--o{ OUTCOMES : resolves_to
    
    MARKET_REGIMES ||--o{ PREDICTIONS : conditions
    PORTFOLIO ||--o{ PAPER_TRADES : contains
    
    STOCKS {
        string symbol PK
        string name
        string sector
        string industry
        string exchange
        decimal market_cap
        boolean is_active
        date delisted_date
        string delisted_reason
    }
    
    PRICES {
        string symbol FK
        date date PK
        decimal open
        decimal high
        decimal low
        decimal close
        decimal adj_close
        bigint volume
        decimal dividend
        decimal split_factor
    }
    
    FUNDAMENTALS {
        string symbol FK
        date period_end PK
        date reported_date
        decimal revenue
        decimal net_income
        decimal eps
        decimal book_value
        decimal total_debt
        decimal total_equity
        decimal current_assets
        decimal current_liabilities
        decimal gross_profit
        decimal operating_income
    }
    
    CORPORATE_ACTIONS {
        int action_id PK
        string symbol FK
        date ex_date
        date announced_date
        string action_type
        decimal ratio
        decimal amount
    }
    
    FEATURES {
        string symbol FK
        date prediction_date PK
        string feature_version PK
        jsonb feature_values
        string feature_hash
    }
    
    LABELS {
        string symbol FK
        date prediction_date PK
        string label_version PK
        int label_3class
        int label_2class
        decimal future_return
    }
    
    MODELS {
        string model_id PK
        string algorithm
        string version
        string feature_version FK
        string label_version FK
        string dataset_version FK
        jsonb hyperparameters
        jsonb metrics
        date trained_date
        string status
        string artifact_path
    }
    
    PREDICTIONS {
        string prediction_id PK
        string symbol FK
        timestamp prediction_timestamp
        string model_id FK
        string feature_version FK
        int horizon_days
        decimal p_up
        decimal p_down
        decimal p_sideways
        decimal confidence
        decimal expected_return
        int predicted_class
        string feature_hash
        string regime
    }
    
    OUTCOMES {
        string prediction_id FK
        timestamp outcome_timestamp
        decimal actual_return
        int actual_class
        boolean correct
        decimal pnl
    }
    
    PAPER_TRADES {
        string trade_id PK
        string symbol FK
        timestamp entry_date
        timestamp exit_date
        string side
        decimal entry_price
        decimal exit_price
        int shares
        decimal pnl
        decimal commission
        decimal slippage
        string prediction_id FK
        string model_id FK
    }
    
    EXPERIMENTS {
        string experiment_id PK
        string name
        string description
        string dataset_version FK
        string model_config
        jsonb metrics
        date created_date
        string status
    }
    
    BACKTESTS {
        string backtest_id PK
        string model_id FK
        string config_hash
        jsonb results
        date start_date
        date end_date
    }
    
    MARKET_REGIMES {
        date date PK
        int hmm_state
        int vol_regime
        decimal vix
        decimal yield_curve
        string trend
    }
    
    PORTFOLIO {
        date date PK
        decimal cash
        decimal positions_value
        decimal total_value
        decimal daily_pnl
        jsonb positions
    }
    
    SYSTEM_LOGS {
        int log_id PK
        timestamp timestamp
        string level
        string component
        string message
        jsonb metadata
    }
`

## Table Definitions

### Core Tables

#### stocks
`sql
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(20),
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    delisted_date DATE,
    delisted_reason VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_active ON stocks(is_active);
`

#### prices (Partitioned by date)
`sql
CREATE TABLE prices (
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,4) NOT NULL,
    high DECIMAL(10,4) NOT NULL,
    low DECIMAL(10,4) NOT NULL,
    close DECIMAL(10,4) NOT NULL,
    adj_close DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    dividend DECIMAL(10,4) DEFAULT 0,
    split_factor DECIMAL(10,6) DEFAULT 1,
    PRIMARY KEY (symbol, date)
) PARTITION BY RANGE (date);

-- Create monthly partitions
CREATE TABLE prices_2024_01 PARTITION OF prices FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- ... etc

CREATE INDEX idx_prices_symbol_date ON prices(symbol, date DESC);
CREATE INDEX idx_prices_date ON prices(date);
`

#### fundamentals
`sql
CREATE TABLE fundamentals (
    symbol VARCHAR(10) NOT NULL,
    period_end DATE NOT NULL,
    reported_date DATE,
    revenue BIGINT,
    net_income BIGINT,
    eps DECIMAL(10,4),
    book_value BIGINT,
    total_debt BIGINT,
    total_equity BIGINT,
    current_assets BIGINT,
    current_liabilities BIGINT,
    gross_profit BIGINT,
    operating_income BIGINT,
    PRIMARY KEY (symbol, period_end)
);
CREATE INDEX idx_fundamentals_reported ON fundamentals(reported_date);
`

#### corporate_actions
`sql
CREATE TABLE corporate_actions (
    action_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    ex_date DATE NOT NULL,
    announced_date DATE,
    action_type VARCHAR(20) NOT NULL,  -- SPLIT, DIVIDEND, MERGER, SPINOFF
    ratio DECIMAL(10,6),  -- for splits
    amount DECIMAL(10,4),  -- for dividends
    details JSONB,
    UNIQUE(symbol, ex_date, action_type)
);
CREATE INDEX idx_actions_symbol ON corporate_actions(symbol);
CREATE INDEX idx_actions_ex_date ON corporate_actions(ex_date);
`

### ML Tables

#### features (Offline feature store)
`sql
CREATE TABLE features (
    symbol VARCHAR(10) NOT NULL,
    prediction_date DATE NOT NULL,
    feature_version VARCHAR(20) NOT NULL,
    feature_values JSONB NOT NULL,
    feature_hash VARCHAR(64) NOT NULL,
    computed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, prediction_date, feature_version)
) PARTITION BY RANGE (prediction_date);

CREATE INDEX idx_features_version ON features(feature_version);
CREATE INDEX idx_features_date ON features(prediction_date);
`

#### labels
`sql
CREATE TABLE labels (
    symbol VARCHAR(10) NOT NULL,
    prediction_date DATE NOT NULL,
    label_version VARCHAR(20) NOT NULL,
    label_3class SMALLINT NOT NULL,  -- 0=DOWN, 1=SIDEWAYS, 2=UP
    label_2class SMALLINT NOT NULL,  -- 0=NOT_PROFITABLE, 1=PROFITABLE
    future_return DECIMAL(10,6),
    PRIMARY KEY (symbol, prediction_date, label_version)
);
CREATE INDEX idx_labels_version ON labels(label_version);
`

#### models
`sql
CREATE TABLE models (
    model_id VARCHAR(50) PRIMARY KEY,
    algorithm VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    feature_version VARCHAR(20) REFERENCES features(feature_version),
    label_version VARCHAR(20) REFERENCES labels(label_version),
    dataset_version VARCHAR(100) NOT NULL,
    hyperparameters JSONB NOT NULL,
    metrics JSONB NOT NULL,
    trained_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,  -- candidate, shadow, production, archived
    artifact_path VARCHAR(500),
    promoted_date TIMESTAMP,
    demoted_date TIMESTAMP
);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_algorithm ON models(algorithm);
`

#### predictions
`sql
CREATE TABLE predictions (
    prediction_id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol),
    prediction_timestamp TIMESTAMP NOT NULL,
    model_id VARCHAR(50) REFERENCES models(model_id),
    feature_version VARCHAR(20) NOT NULL,
    horizon_days SMALLINT NOT NULL,
    p_up DECIMAL(6,4) NOT NULL,
    p_down DECIMAL(6,4) NOT NULL,
    p_sideways DECIMAL(6,4) NOT NULL,
    confidence DECIMAL(6,4) NOT NULL,
    expected_return DECIMAL(10,6),
    predicted_class SMALLINT NOT NULL,
    feature_hash VARCHAR(64) NOT NULL,
    regime SMALLINT,
    vol_regime SMALLINT,
    rank_up INTEGER,
    rank_expected_return INTEGER,
    risk_score DECIMAL(6,4),
    position_size_pct DECIMAL(6,4),
    no_trade_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_predictions_symbol_date ON predictions(symbol, prediction_timestamp);
CREATE INDEX idx_predictions_model ON predictions(model_id);
CREATE INDEX idx_predictions_date ON predictions(prediction_timestamp);
`

#### outcomes
`sql
CREATE TABLE outcomes (
    prediction_id VARCHAR(50) PRIMARY KEY REFERENCES predictions(prediction_id),
    outcome_timestamp TIMESTAMP NOT NULL,
    actual_return DECIMAL(10,6) NOT NULL,
    actual_class SMALLINT NOT NULL,
    correct BOOLEAN NOT NULL,
    pnl DECIMAL(10,6),
    resolved_at TIMESTAMP DEFAULT NOW()
);
`

#### paper_trades
`sql
CREATE TABLE paper_trades (
    trade_id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol),
    entry_date TIMESTAMP NOT NULL,
    exit_date TIMESTAMP,
    side VARCHAR(10) NOT NULL,  -- BUY, SELL
    entry_price DECIMAL(10,4) NOT NULL,
    exit_price DECIMAL(10,4),
    shares INTEGER NOT NULL,
    pnl DECIMAL(12,2),
    commission DECIMAL(10,2),
    spread_cost DECIMAL(10,2),
    slippage DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    prediction_id VARCHAR(50) REFERENCES predictions(prediction_id),
    model_id VARCHAR(50) REFERENCES models(model_id),
    status VARCHAR(20) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_trades_entry ON paper_trades(entry_date);
CREATE INDEX idx_trades_status ON paper_trades(status);
`

#### experiments
`sql
CREATE TABLE experiments (
    experiment_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_version VARCHAR(100) NOT NULL,
    model_config JSONB NOT NULL,
    metrics JSONB,
    created_date TIMESTAMP DEFAULT NOW(),
    completed_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING',  -- RUNNING, COMPLETED, FAILED
    tags TEXT[]
);
CREATE INDEX idx_experiments_dataset ON experiments(dataset_version);
CREATE INDEX idx_experiments_status ON experiments(status);
`

#### backtests
`sql
CREATE TABLE backtests (
    backtest_id VARCHAR(50) PRIMARY KEY,
    model_id VARCHAR(50) REFERENCES models(model_id),
    config_hash VARCHAR(64) NOT NULL,
    results JSONB NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
`

#### market_regimes
`sql
CREATE TABLE market_regimes (
    date DATE PRIMARY KEY,
    hmm_state SMALLINT,  -- 0=bear, 1=sideways, 2=bull
    vol_regime SMALLINT,  -- 0=low, 1=high
    vix DECIMAL(6,2),
    yield_curve DECIMAL(6,2),
    trend VARCHAR(20),
    spy_above_sma20 BOOLEAN,
    spy_above_sma50 BOOLEAN,
    spy_above_sma200 BOOLEAN
);
`

#### portfolio (Daily snapshots)
`sql
CREATE TABLE portfolio (
    date DATE PRIMARY KEY,
    cash DECIMAL(15,2) NOT NULL,
    positions_value DECIMAL(15,2) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    daily_pnl DECIMAL(15,2),
    daily_return DECIMAL(10,6),
    positions JSONB,
    gross_exposure DECIMAL(10,4),
    net_exposure DECIMAL(10,4),
    n_positions SMALLINT,
    max_drawdown DECIMAL(6,4),
    current_drawdown DECIMAL(6,4)
);
`

#### system_logs
`sql
CREATE TABLE system_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_level ON system_logs(level);
`

## Data Flow & Consistency

### Prediction Logging (Write Path)
`python
def log_prediction(prediction):
    # Single transaction
    with db.transaction():
        # 1. Insert prediction (immutable)
        db.insert('predictions', prediction)
        
        # 2. Queue outcome resolution job
        queue.enqueue('resolve_outcome', prediction.prediction_id, prediction.horizon_days)
`

### Outcome Resolution (Async)
`python
def resolve_outcome(prediction_id, horizon_days):
    prediction = db.get('predictions', prediction_id)
    outcome_date = next_trading_day(prediction.prediction_timestamp + horizon_days)
    
    if outcome_date <= now():
        entry_price = get_price(prediction.symbol, prediction.prediction_timestamp)
        exit_price = get_price(prediction.symbol, outcome_date)
        
        if entry_price and exit_price:
            actual_return = exit_price / entry_price - 1
            actual_class = classify_return(actual_return)
            
            outcome = {
                'prediction_id': prediction_id,
                'outcome_timestamp': outcome_date,
                'actual_return': actual_return,
                'actual_class': actual_class,
                'correct': (prediction.predicted_class == actual_class),
                'pnl': actual_return * prediction.position_size_pct
            }
            db.insert('outcomes', outcome)
`

## Migration Strategy

1. **Schema Versioning**: Use Alembic or similar
2. **Backward Compatibility**: Add columns, never remove
3. **Partition Management**: Automated monthly partition creation
4. **Index Management**: Monitor query plans, add indexes as needed
5. **Archival**: Move old partitions to cold storage after 2 years

## Summary

| Table | Primary Key | Partitioning | Retention |
|-------|-------------|--------------|-----------|
| prices | (symbol, date) | Monthly by date | 10+ years |
| features | (symbol, date, version) | Monthly by date | 5 years |
| labels | (symbol, date, version) | Monthly by date | 5 years |
| predictions | prediction_id | Monthly by timestamp | 5 years |
| outcomes | prediction_id | Monthly by timestamp | 5 years |
| paper_trades | trade_id | Monthly by entry_date | 3 years |
| system_logs | log_id | Monthly by timestamp | 1 year |
| models | model_id | None | Forever |
| experiments | experiment_id | None | Forever |
| backtests | backtest_id | None | Forever |
| portfolio | date | None | Forever |
| market_regimes | date | None | Forever |
