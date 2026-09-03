"""
Data Validation Schemas

Pydantic models for data validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

class OHLCVSchema(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    timestamp: datetime
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    vwap: Optional[float] = None
    transactions: Optional[int] = None

    @field_validator("high")
    @classmethod
    def high_ge_low(cls, v, info):
        if "low" in info.data and v < info.data["low"]:
            raise ValueError("High must be >= Low")
        return v

    @field_validator("low")
    @classmethod
    def low_le_high(cls, v, info):
        if "high" in info.data and v > info.data["high"]:
            raise ValueError("Low must be <= High")
        return v

    @field_validator("open", "close")
    @classmethod
    def open_close_in_range(cls, v, info):
        if "low" in info.data and "high" in info.data:
            if not (info.data["low"] <= v <= info.data["high"]):
                raise ValueError("Open/Close must be within High-Low range")
        return v
