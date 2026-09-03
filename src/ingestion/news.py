"""
News Data Ingestion Module

NewsAPI / RSS ingestion with entity linking
"""

import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class NewsArticle:
    title: str
    url: str
    source: str
    published_at: pd.Timestamp
    content: Optional[str] = None
    symbols: List[str] = None
    sentiment_score: Optional[float] = None

class NewsProvider:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_news(self, symbols: List[str], start: pd.Timestamp, end: pd.Timestamp) -> List[NewsArticle]:
        return []

