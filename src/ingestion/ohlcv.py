"""
OHLCV Data Ingestion Module

Supports multiple data providers with failover:
Polygon.io primary
Yahoo Finance fallback
Alpha Vantage fallback
"""

import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class OHLCVBar:
    """Single OHLCV bar"""
    symbol: str
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap = None
    transactions = None

class DataProvider(ABC):
    @abstractmethod
    async def fetch_bars(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day") -> List[OHLCVBar]:
        pass
    @abstractmethod
    async def fetch_snapshot(self, symbol: str):
        pass
    @abstractmethod
    def get_name(self) -> str:
        pass

class PolygonProvider(DataProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_name(self) -> str:
        return "polygon"

    def _build_url(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str) -> str:
        mult = 1
        from_str = start.strftime("%Y-%m-%d")
        to_str = end.strftime("%Y-%m-%d")
        return ("{self.base_url}/v2/aggs/ticker/{symbol}/range/{mult}/{timespan}"
            "/{from_str}/{to_str}?adjusted=true&sort=asc&limit=50000&apiKey={self.api_key}")

    async def fetch_bars(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day") -> List[OHLCVBar]:
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = self._build_url(symbol, start, end, timespan)
        async with self.session.get(url) as resp:
            if resp.status == 429:
                raise Exception("Polygon rate limit exceeded")
            if resp.status != 200:
                text = await resp.text()
                raise Exception("Polygon API error {resp.status}: {text}")
            data = await resp.json()

            if data.get("status") != "OK" or "results" not in data:
                return []

            bars = []
            for r in data["results"]:
                bars.append(OHLCVBar(symbol=symbol, timestamp=pd.Timestamp(r["t"], unit="ms", tz="UTC").tz_convert("US/Eastern"), open=float(r["o"]), high=float(r["h"]), low=float(r["l"]), close=float(r["c"]), volume=int(r["v"])))
            return bars

    async def fetch_snapshot(self, symbol: str):
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = "{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={self.api_key}"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            ticker = data.get("ticker", {})
            day = ticker.get("day", {})
            if not day:
                return None
            return OHLCVBar(symbol=symbol, timestamp=pd.Timestamp.now(tz="US/Eastern"), open=float(day.get("o", 0)), high=float(day.get("h", 0)), low=float(day.get("l", 0)), close=float(day.get("c", 0)), volume=int(day.get("v", 0)))

class YahooProvider(DataProvider):
    def __init__(self, base_url: str = "https://query1.finance.yahoo.com"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_name(self) -> str:
        return "yahoo"

    def _build_url(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, interval: str = "1d") -> str:
        period1 = int(start.timestamp())
        period2 = int(end.timestamp())
        return ("{self.base_url}/v8/finance/chart/{symbol}"
            "?period1={period1}&period2={period2}&interval={interval}&includePrePost=false")

    async def fetch_bars(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day") -> List[OHLCVBar]:
        if not self.session:
            self.session = aiohttp.ClientSession()
        interval_map = {"day": "1d", "hour": "1h", "minute": "1m"}
        interval = interval_map.get(timespan, "1d")
        url = self._build_url(symbol, start, end, interval)
        async with self.session.get(url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception("Yahoo API error {resp.status}: {text}")
            data = await resp.json()

            chart = data.get("chart", {})
            result = chart.get("result", [])
            if not result:
                return []

            result = result[0]
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            adjclose = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
            opens = quotes.get("open", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])
            closes = quotes.get("close", [])
            volumes = quotes.get("volume", [])

            bars = []
            for i, ts in enumerate(timestamps):
                if any(v is None for v in [opens[i], highs[i], lows[i], closes[i], volumes[i]]):
                    continue
                close_price = adjclose[i] if i < len(adjclose) and adjclose[i] is not None else closes[i]
                bars.append(OHLCVBar(symbol=symbol, timestamp=pd.Timestamp(ts, unit="s", tz="UTC").tz_convert("US/Eastern"), open=float(opens[i]), high=float(highs[i]), low=float(lows[i]), close=float(close_price), volume=int(volumes[i])))
            return bars

    async def fetch_snapshot(self, symbol: str):
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = "{self.base_url}/v8/finance/chart/{symbol}?interval=1d&range=1d"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            result = result[0]
            meta = result.get("meta", {})
            return OHLCVBar(symbol=symbol, timestamp=pd.Timestamp.now(tz="US/Eastern"), open=float(meta.get("regularMarketOpen", 0)), high=float(meta.get("regularMarketDayHigh", 0)), low=float(meta.get("regularMarketDayLow", 0)), close=float(meta.get("regularMarketPrice", 0)), volume=int(meta.get("regularMarketVolume", 0)))

class AlphaVantageProvider(DataProvider):
    def __init__(self, api_key: str, base_url: str = "https://www.alphavantage.co"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_name(self) -> str:
        return "alphavantage"

    def _build_url(self, symbol: str, outputsize: str = "full") -> str:
        return ("{self.base_url}/query?function=TIME_SERIES_DAILY_ADJUSTED"
            "&symbol={symbol}&outputsize={outputsize}&apikey={self.api_key}")

    async def fetch_bars(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day") -> List[OHLCVBar]:
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = self._build_url(symbol)
        async with self.session.get(url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception("Alpha Vantage API error {resp.status}: {text}")
            data = await resp.json()

            if "Error Message" in data:
                raise Exception("Alpha Vantage error: {data[Error Message]}")
            if "Note" in data:
                raise Exception("Alpha Vantage rate limit: {data[Note]}")
            time_series = data.get("Time Series (Daily)", {})
            if not time_series:
                return []

            bars = []
            for date_str, values in time_series.items():
                ts = pd.Timestamp(date_str, tz="US/Eastern")
                if ts < start or ts > end:
                    continue
                bars.append(OHLCVBar(symbol=symbol, timestamp=ts, open=float(values["1. open"]), high=float(values["2. high"]), low=float(values["3. low"]), close=float(values["5. adjusted close"]), volume=int(values["6. volume"])))
            bars.sort(key=lambda x: x.timestamp)
            return bars

    async def fetch_snapshot(self, symbol: str):
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = "{self.base_url}/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            quote = data.get("Global Quote", {})
            if not quote:
                return None
            return OHLCVBar(symbol=symbol, timestamp=pd.Timestamp.now(tz="US/Eastern"), open=float(quote.get("02. open", 0)), high=float(quote.get("03. high", 0)), low=float(quote.get("04. low", 0)), close=float(quote.get("05. price", 0)), volume=int(quote.get("06. volume", 0)))

class OHLCVIngestion:
    def __init__(self):
        self.providers = []
        self._init_providers()

    def _init_providers(self):
        cfg = settings.data_providers
        if cfg.primary == "polygon" and cfg.polygon.api_key:
            self.providers.append(PolygonProvider(cfg.polygon.api_key, cfg.polygon.base_url))
        elif cfg.primary == "yahoo":
            self.providers.append(YahooProvider(cfg.yahoo.base_url))
        elif cfg.primary == "alphavantage" and cfg.alphavantage.api_key:
            self.providers.append(AlphaVantageProvider(cfg.alphavantage.api_key, cfg.alphavantage.base_url))

        for fallback in cfg.fallback:
            if fallback == "polygon" and cfg.polygon.api_key:
                self.providers.append(PolygonProvider(cfg.polygon.api_key, cfg.polygon.base_url))
            elif fallback == "yahoo":
                self.providers.append(YahooProvider(cfg.yahoo.base_url))
            elif fallback == "alphavantage" and cfg.alphavantage.api_key:
                self.providers.append(AlphaVantageProvider(cfg.alphavantage.api_key, cfg.alphavantage.base_url))

    async def fetch_bars(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day") -> List[OHLCVBar]:
        last_error = None
        for provider in self.providers:
            async with provider:
                try:
                    bars = await provider.fetch_bars(symbol, start, end, timespan)
                    if bars:
                        return bars
                except Exception as e:
                    last_error = e
                    continue
        raise Exception("All providers failed for {symbol}. Last error: {last_error}")

    async def fetch_snapshot(self, symbol: str):
        for provider in self.providers:
            async with provider:
                try:
                    snapshot = await provider.fetch_snapshot(symbol)
                    if snapshot:
                        return snapshot
                except Exception as e:
                    continue
        return None

    async def fetch_universe(self, symbols: List[str], start: pd.Timestamp, end: pd.Timestamp, timespan: str = "day", max_concurrent: int = 5) -> Dict[str, List[OHLCVBar]]:
        semaphore = asyncio.Semaphore(max_concurrent)
        async def fetch_one(symbol: str):
            async with semaphore:
                try:
                    bars = await self.fetch_bars(symbol, start, end, timespan)
                    return symbol, bars
                except Exception as e:
                    return symbol, []
        tasks = [fetch_one(sym) for sym in symbols]
        results = await asyncio.gather(*tasks)
        return dict(results)

async def main():
    ingestion = OHLCVIngestion()
    symbols = ["AAPL", "MSFT", "GOOGL"]
    start = pd.Timestamp("2024-01-01", tz="US/Eastern")
    end = pd.Timestamp("2024-01-31", tz="US/Eastern")

    results = await ingestion.fetch_universe(symbols, start, end)

    for symbol, bars in results.items():
        print("{symbol}: {len(bars)} bars".format(symbol=symbol, len=len(bars)))
        if bars:
            print("  First: {bars[0]}".format(bars=bars))
            print("  Last: {bars[-1]}".format(bars=bars))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
