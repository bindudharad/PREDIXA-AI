import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "predixa"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def url(self) -> str:
        return "postgresql://" + self.user + ":" + self.password + "@" + self.host + ":" + str(self.port) + "/" + self.name

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""

class MLflowConfig(BaseModel):
    tracking_uri: str = "http://localhost:5000"
    artifact_uri: str = "s3://predixa-mlflow/artifacts"

class S3Config(BaseModel):
    endpoint: str = "http://localhost:9000"
    access_key: str = ""
    secret_key: str = ""
    bucket: str = "predixa-data"

class PolygonConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.polygon.io"

class YahooConfig(BaseModel):
    base_url: str = "https://query1.finance.yahoo.com"

class AlphaVantageConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://www.alphavantage.co"

class DataProvidersConfig(BaseModel):
    primary: str = "polygon"
    fallback: List[str] = Field(default_factory=lambda: ["yahoo", "alphavantage"])
    polygon: PolygonConfig = Field(default_factory=PolygonConfig)
    yahoo: YahooConfig = Field(default_factory=YahooConfig)
    alphavantage: AlphaVantageConfig = Field(default_factory=AlphaVantageConfig)

class UniverseConfig(BaseModel):
    name: str = "sp500_liquid"
    min_market_cap: float = 2000000000.0
    min_avg_volume: int = 500000
    min_price: float = 5.0

class LagConfig(BaseModel):
    fundamentals_days: int = 60
    news_days: int = 1
    macro_days: int = 1
    market_relative_days: int = 1

class FeaturesConfig(BaseModel):
    version: str = "feat_v1.0"
    lag_config: LagConfig = Field(default_factory=LagConfig)

class LabelThresholds(BaseModel):
    up: float = 0.02
    down: float = 0.02
    sideways: float = 0.01

class LabelsConfig(BaseModel):
    version: str = "label_v1.0"
    horizons: List[int] = Field(default_factory=lambda: [1, 5, 10, 20, 60])
    thresholds: LabelThresholds = Field(default_factory=LabelThresholds)

class WalkForwardConfig(BaseModel):
    method: str = "expanding"
    n_folds: int = 5
    embargo_days: int = 30
    val_months: int = 3
    test_months: int = 3

class HPOConfig(BaseModel):
    n_trials: int = 100
    timeout: int = 3600

class TrainingConfig(BaseModel):
    walkforward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    hpo: HPOConfig = Field(default_factory=HPOConfig)

class CostsConfig(BaseModel):
    commission_per_share: float = 0.005
    commission_min: float = 1.0
    spread_bps: float = 10
    slippage_bps: float = 5
    slippage_model: str = "square_root"

class SizingConfig(BaseModel):
    method: str = "fixed_fractional"
    max_position_pct: float = 0.05

class ConstraintsConfig(BaseModel):
    max_position_pct: float = 0.10
    max_sector_pct: float = 0.30
    max_gross_exposure: float = 1.0
    max_turnover_monthly: float = 2.0

class BacktestConfig(BaseModel):
    entry_rule: str = "next_open"
    exit_rule: str = "fixed_horizon"
    costs: CostsConfig = Field(default_factory=CostsConfig)
    sizing: SizingConfig = Field(default_factory=SizingConfig)
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)

class DriftConfig(BaseModel):
    prediction_psi_threshold: float = 0.25
    feature_psi_threshold: float = 0.20
    ece_threshold: float = 0.05
    logloss_increase_threshold: float = 0.10

class MonitoringConfig(BaseModel):
    drift: DriftConfig = Field(default_factory=DriftConfig)
    performance_window_days: int = 30
    alert_channels: List[str] = Field(default_factory=lambda: ["slack", "email"])

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "predixa-ai"
    app_version: str = "0.1.0"
    environment: str = "development"

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    mlflow: MLflowConfig = Field(default_factory=MLflowConfig)
    s3: S3Config = Field(default_factory=S3Config)
    data_providers: DataProvidersConfig = Field(default_factory=DataProvidersConfig)
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    labels: LabelsConfig = Field(default_factory=LabelsConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "Settings":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        flat = {}
        def flatten(d, prefix=""):
            for k, v in d.items():
                key = prefix + k
                if isinstance(v, dict):
                    flatten(v, key + "_")
                else:
                    flat[key] = v
        flatten(data.get("app", {}))
        flatten(data.get("database", {}), "database_")
        flatten(data.get("redis", {}), "redis_")
        flatten(data.get("mlflow", {}), "mlflow_")
        flatten(data.get("s3", {}), "s3_")
        flatten(data.get("data_providers", {}), "data_providers_")
        flatten(data.get("universe", {}), "universe_")
        flatten(data.get("features", {}), "features_")
        flatten(data.get("labels", {}), "labels_")
        flatten(data.get("training", {}), "training_")
        flatten(data.get("backtest", {}), "backtest_")
        flatten(data.get("monitoring", {}), "monitoring_")
        return cls(**flat)

    def to_yaml(self, path: str) -> None:
        data = self.model_dump()
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

settings = Settings()

def load_settings(config_path: Optional[str] = None) -> Settings:
    global settings
    if config_path and os.path.exists(config_path):
        settings = Settings.from_yaml(config_path)
    return settings

def get_settings() -> Settings:
    return settings
