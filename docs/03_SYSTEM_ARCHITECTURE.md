# 03_SYSTEM_ARCHITECTURE.md

## System Architecture Overview

The PREDIXA AI system follows a modular pipeline architecture where data flows through well-defined stages, each with clear inputs, outputs, and validation checks. The architecture emphasizes **temporal integrity** (no look-ahead bias), **reproducibility** (versioned artifacts), and **observability** (monitoring at every stage).

## High-Level Architecture

`mermaid
flowchart TD
    subgraph DataSources [Data Sources]
        DS1[Market Data Providers\nYahoo, Alpha Vantage, Polygon]
        DS2[Fundamental Data\nSEC, Financial APIs]
        DS3[News/Sentiment\nRSS, NewsAPI, FinBERT]
        DS4[Macro Data\nFRED, Treasury, VIX]
    end

    subgraph Ingestion [Data Ingestion Layer]
        DI1[OHLCV Ingestion]
        DI2[Corporate Actions]
        DI3[Fundamental Ingestion]
        DI4[News Ingestion]
        DI5[Macro Ingestion]
    end

    subgraph Validation [Data Validation & Quality]
        DV1[Schema Validation]
        DV2[Range/Continuity Checks]
        DV3[Outlier Detection]
        DV4[Quality Reports]
    end

    subgraph Storage [Data Storage]
        ST1[(Raw Data Lake\nParquet/Delta Lake)]
        ST2[(Validated Data\nPostgreSQL/TimescaleDB)]
        ST3[(Feature Store\nFeast/Custom)]
        ST4[(Model Registry\nMLflow)]
    end

    subgraph FeatureEng [Feature Engineering]
        FE1[Price Features]
        FE2[Technical Indicators]
        FE3[Volatility Features]
        FE4[Market-Relative Features]
        FE5[Regime Features]
        FE6[Fundamental Features]
        FE7[News/Sentiment Features]
        FE8[Macro Features]
    end

    subgraph LabelGen [Label Generation]
        LG1[Horizon Configuration]
        LG2[Threshold Configuration]
        LG3[Forward Return Calculation]
        LG4[Class Assignment]
    end

    subgraph DatasetBuilder [Dataset Builder]
        DB1[Temporal Split Strategy]
        DB2[Expanding/Rolling Windows]
        DB3[Purged/Embargoed CV]
        DB4[Dataset Versioning]
    end

    subgraph MLPipeline [ML Training Pipeline]
        ML1[Baseline Models\nLogistic Regression]
        ML2[Classical ML\nXGBoost, LightGBM]
        ML3[Deep Learning\nLSTM, Transformer]
        ML4[Hyperparameter Optimization]
        ML5[Model Evaluation]
        ML6[Calibration]
    end

    subgraph ModelRegistry [Model Registry]
        MR1[Model Versioning]
        MR2[Artifact Storage]
        MR3[Metadata/Lineage]
        MR4[Promotion Workflow]
    end

    subgraph PredictionEngine [Prediction Engine]
        PE1[Feature Computation\nat Prediction Time]
        PE2[Model Inference]
        PE3[Probability Calibration]
        PE4[Confidence Scoring]
        PE5[Ranking]
    end

    subgraph RiskEngine [Risk Engine]
        RE1[Position Risk]
        RE2[Portfolio Risk]
        RE3[Liquidity Risk]
        RE4[Model Uncertainty]
        RE5[Risk Limits]
    end

    subgraph RankingEngine [Ranking Engine]
        RK1[Probability Ranking]
        RK2[Expected Return Ranking]
        RK3[Diversification Filters]
        RK4[Liquidity Filters]
    end

    subgraph Agent [Prediction Agent]
        AG1[Technical Agent]
        AG2[News/Sentiment Agent]
        AG3[Risk Agent]
        AG4[Decision Engine]
        AG5[Explainability]
    end

    subgraph APILayer [API Layer]
        API1[REST API\nFastAPI]
        API2[WebSocket/SSE\nReal-time Feed]
        API3[Auth/Rate Limit]
    end

    subgraph Dashboard [Dashboard]
        DH1[Prediction Explorer]
        DH2[Performance Analytics]
        DH3[Model Comparison]
        DH4[Drift Monitoring]
        DH5[Backtest Viewer]
    end

    subgraph Monitoring [Monitoring & Operations]
        MON1[Drift Detection]
        MON2[Performance Tracking]
        MON3[Data Quality Alerts]
        MON4[Retraining Orchestration]
        MON5[Experiment Tracking]
    end

    %% Data flow
    DS1 --> DI1
    DS2 --> DI3
    DS3 --> DI4
    DS4 --> DI5
    
    DI1 --> DV1
    DI2 --> DV1
    DI3 --> DV1
    DI4 --> DV1
    DI5 --> DV1
    
    DV1 --> ST1
    DV2 --> ST2
    DV3 --> ST2
    DV4 --> ST2
    
    ST1 --> FE1
    ST1 --> FE2
    ST1 --> FE3
    ST1 --> FE4
    ST1 --> FE5
    ST2 --> FE6
    ST2 --> FE7
    ST2 --> FE8
    
    FE1 --> DB1
    FE2 --> DB1
    FE3 --> DB1
    FE4 --> DB1
    FE5 --> DB1
    FE6 --> DB1
    FE7 --> DB1
    FE8 --> DB1
    
    LG1 --> DB1
    LG2 --> DB1
    LG3 --> DB1
    LG4 --> DB1
    
    DB1 --> ML1
    DB1 --> ML2
    DB1 --> ML3
    
    ML1 --> ML5
    ML2 --> ML5
    ML3 --> ML5
    ML4 --> ML5
    ML5 --> ML6
    ML6 --> MR1
    
    MR1 --> PE1
    ST3 --> PE1
    PE1 --> PE2
    PE2 --> PE3
    PE3 --> PE4
    PE4 --> PE5
    
    PE5 --> RE1
    RE1 --> RE2
    RE2 --> RE3
    RE3 --> RE4
    RE4 --> RE5
    
    RE5 --> RK1
    RK1 --> RK2
    RK2 --> RK3
    RK3 --> RK4
    
    RK4 --> AG1
    RK4 --> AG2
    RK4 --> AG3
    AG1 --> AG4
    AG2 --> AG4
    AG3 --> AG4
    AG4 --> AG5
    
    AG5 --> API1
    API1 --> API2
    API1 --> API3
    
    API1 --> DH1
    API1 --> DH2
    API1 --> DH3
    API1 --> DH4
    API1 --> DH5
    
    PE1 --> MON1
    PE2 --> MON2
    ST2 --> MON3
    MON1 --> MON4
    MON2 --> MON4
    MON4 --> ML1
    ML5 --> MON5

    classDef source fill:#e1f5fe,stroke:#01579b
    classDef ingestion fill:#f3e5f5,stroke:#4a148c
    classDef validation fill:#fff3e0,stroke:#e65100
    classDef storage fill:#e8f5e9,stroke:#1b5e20
    classDef feature fill:#fce4ec,stroke:#880e4f
    classDef label fill:#f1f8e9,stroke:#33691e
    classDef dataset fill:#ede7f6,stroke:#311b92
    classDef ml fill:#e3f2fd,stroke:#0d47a1
    classDef registry fill:#fff8e1,stroke:#f57f17
    classDef prediction fill:#fbe9e7,stroke:#bf360c
    classDef risk fill:#efebe9,stroke:#3e2723
    classDef ranking fill:#e0f2f1,stroke:#004d40
    classDef agent fill:#fce4ec,stroke:#880e4f
    classDef api fill:#e8eaf6,stroke:#283593
    classDef dashboard fill:#f3e5f5,stroke:#4a148c
    classDef monitor fill:#fff3e0,stroke:#e65100

    class DS1,DS2,DS3,DS4 source
    class DI1,DI2,DI3,DI4,DI5 ingestion
    class DV1,DV2,DV3,DV4 validation
    class ST1,ST2,ST3,ST4 storage
    class FE1,FE2,FE3,FE4,FE5,FE6,FE7,FE8 feature
    class LG1,LG2,LG3,LG4 label
    class DB1,DB2,DB3,DB4 dataset
    class ML1,ML2,ML3,ML4,ML5,ML6 ml
    class MR1,MR2,MR3,MR4 registry
    class PE1,PE2,PE3,PE4,PE5 prediction
    class RE1,RE2,RE3,RE4,RE5 risk
    class RK1,RK2,RK3,RK4 ranking
    class AG1,AG2,AG3,AG4,AG5 agent
    class API1,API2,API3 api
    class DH1,DH2,DH3,DH4,DH5 dashboard
    class MON1,MON2,MON3,MON4,MON5 monitor
`

## Component Descriptions

### 1. Data Sources
External data providers supplying raw market data. Multiple providers for redundancy and cross-validation.

### 2. Data Ingestion Layer
- **OHLCV Ingestion**: Batch and incremental collection of price/volume data
- **Corporate Actions**: Splits, dividends, mergers for price adjustment
- **Fundamental Ingestion**: Quarterly/annual financial statements
- **News Ingestion**: Article collection with entity linking to tickers
- **Macro Ingestion**: Economic indicators, rates, volatility indices

### 3. Data Validation & Quality
- **Schema Validation**: Enforce column types, constraints, required fields
- **Range/Continuity Checks**: Price > 0, high >= low, no missing trading days
- **Outlier Detection**: Statistical and ML-based anomaly flagging
- **Quality Reports**: Per-run data quality metrics and alerts

### 4. Data Storage
- **Raw Data Lake**: Immutable raw data in Parquet/Delta Lake (append-only)
- **Validated Data**: Cleaned, adjusted data in TimescaleDB (time-series optimized)
- **Feature Store**: Computed features with versioning for training/inference consistency
- **Model Registry**: MLflow-based model versioning, artifacts, metadata

### 5. Feature Engineering
Eight feature groups computed **only from data available at prediction time**:
- Price features (returns, momentum, gaps, ranges)
- Technical indicators (SMA, EMA, RSI, MACD, BB, ATR, volume)
- Volatility features (rolling vol, regime, GARCH forecasts)
- Market-relative (vs index, vs sector, beta, relative strength)
- Regime features (HMM states, bull/bear/sideways, vol regime)
- Fundamental (EPS, revenue, P/E, P/B, ROE, D/E - quarterly lagged)
- News/sentiment (count, score, recency, intensity - lagged)
- Macro (VIX, yield curve, DXY, commodities - lagged)

### 6. Label Generation
- Configurable horizons (1D, 5D, 10D, 20D, 60D trading days)
- Configurable thresholds (e.g., ±1%, ±2%, ±3% for UP/DOWN)
- 3-class: UP (>threshold), DOWN (<-threshold), SIDEWAYS (between)
- 2-class: PROFITABLE (>0), NOT_PROFITABLE (<=0)
- Entry: close of prediction date; Exit: close of prediction date + horizon

### 7. Dataset Builder
- **Temporal Splits Only**: No random shuffling
- **Expanding Window**: Training grows, validation/test fixed forward
- **Rolling Window**: Fixed training window size, slides forward
- **Purged/Embargoed**: Gap between train/validation to prevent leakage
- **Versioning**: Dataset hash + config hash = reproducible identifier

### 8. ML Training Pipeline
- **Baseline**: Logistic Regression, Random Forest (benchmark)
- **Classical ML**: XGBoost, LightGBM, CatBoost (primary)
- **Deep Learning**: LSTM, GRU, Temporal CNN, Transformer (if justified)
- **HPO**: Optuna with temporal CV
- **Evaluation**: Classification + probabilistic metrics on held-out test
- **Calibration**: Platt scaling / isotonic regression on validation set

### 9. Model Registry
- Versioned model artifacts (model.pkl, config.yaml, metrics.json)
- Lineage: dataset version, feature version, hyperparameters
- Promotion workflow: candidate -> validation -> shadow -> production
- Rollback capability

### 10. Prediction Engine
- Computes features at prediction time (same code as training)
- Loads production model from registry
- Outputs calibrated probabilities for all classes
- Confidence score (entropy-based or calibration-based)
- Ranks universe by probability/expected return

### 11. Risk Engine
- Position-level: VaR, expected shortfall, max loss per trade
- Portfolio-level: correlation, factor exposure, concentration limits
- Liquidity: days to liquidate, market impact estimation
- Model uncertainty: prediction entropy, prediction intervals
- Hard risk limits (veto power in agent)

### 12. Ranking Engine
- Primary: P(UP) descending
- Secondary: Expected return (probability-weighted)
- Filters: min confidence, min liquidity, max sector concentration
- Output: ordered list with metadata for agent

### 13. Prediction Agent
- **Technical Agent**: Price/volume model output + confidence
- **News Agent**: Sentiment model output + confidence
- **Risk Agent**: Risk constraints + position limits
- **Decision Engine**: Weighted combination, veto logic, no-trade rules
- **Explainability**: SHAP values, feature attribution per prediction

### 14. API Layer
- REST API (FastAPI): predictions, performance, models, health
- WebSocket/SSE: real-time prediction updates
- Authentication: API keys, JWT
- Rate limiting, input validation

### 15. Dashboard
- Prediction explorer (historical + live)
- Performance analytics (metrics, calibration, attribution)
- Model comparison (production vs candidates)
- Drift monitoring (feature, prediction, performance)
- Backtest viewer (trade analysis, equity curves)

### 16. Monitoring & Operations
- **Drift Detection**: PSI, KS test, ADWIN on features/predictions/performance
- **Performance Tracking**: Rolling metrics, regime-conditional
- **Data Quality Alerts**: Completeness, latency, anomalies
- **Retraining Orchestration**: Scheduled + trigger-based
- **Experiment Tracking**: MLflow integration for all experiments

## Data Flow Guarantees

1. **Temporal Integrity**: Every component receives only data with timestamp ≤ prediction timestamp
2. **Version Consistency**: Features at inference match features at training (feature store)
3. **Audit Trail**: Every prediction logged with model version, feature hash, timestamp
4. **Reproducibility**: Dataset hash + config hash uniquely identifies any experiment
5. **Immutable Raw Data**: Raw data never modified; corrections via new versions

## Deployment Architecture

`mermaid
flowchart LR
    subgraph Cloud [Cloud Infrastructure]
        subgraph Compute [Compute]
            K8s[Kubernetes Cluster]
            GPU[GPU Nodes for DL]
            CPU[CPU Nodes for Classical ML]
        end
        
        subgraph Storage [Storage]
            S3[S3/MinIO\nData Lake]
            PG[PostgreSQL/TimescaleDB]
            Redis[Redis\nCache/Queue]
            MLflow[MLflow Server]
        end
        
        subgraph Services [Services]
            API[API Pods\nHorizontal Scaling]
            Worker[Worker Pods\nFeature/Inference]
            Scheduler[Scheduler\nCron/Triggers]
            Monitor[Monitoring\nPrometheus/Grafana]
        end
    end
    
    User[Users/Dashboard] --> API
    API --> Worker
    Worker --> S3
    Worker --> PG
    Worker --> Redis
    Scheduler --> Worker
    MLflow --> S3
    MLflow --> PG
    Monitor --> API
    Monitor --> Worker
`

## Technology Mapping

| Component | Technology | Justification |
|-----------|------------|---------------|
| API Framework | FastAPI | Async, auto-docs, type safety, performance |
| Data Processing | Pandas, Polars | Polars for speed, Pandas for compatibility |
| Time-series DB | TimescaleDB | PostgreSQL-compatible, hypertables, compression |
| Feature Store | Feast or Custom | Versioned features, online/offline serving |
| ML Framework | Scikit-learn, XGBoost, LightGBM | Mature, fast, well-tested |
| Deep Learning | PyTorch | Flexible, good for research |
| Experiment Tracking | MLflow | Standard, integrates with registry |
| Orchestration | Apache Airflow / Prefect | DAG-based, retries, monitoring |
| Containerization | Docker + Kubernetes | Scalable, reproducible |
| Monitoring | Prometheus + Grafana | Standard, powerful alerting |
| Dashboard | React + Plotly/Dash | Interactive, real-time capable |
| Message Queue | Redis / RabbitMQ | Async task processing |

## Critical Design Principles

1. **No Future Data**: Every pipeline stage enforces temporal boundaries
2. **Explicit Versioning**: Data, features, models, datasets all versioned
3. **Separation of Concerns**: Prediction ≠ Trading; Research ≠ Production
4. **Observability First**: Metrics, logs, traces at every stage
5. **Fail-Safe Defaults**: Conservative risk limits, no-trade on uncertainty
6. **Human-in-the-Loop**: Model promotion requires approval
7. **Cost Awareness**: Transaction costs modeled from day one

---
