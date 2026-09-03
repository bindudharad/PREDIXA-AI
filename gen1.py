import os; os.makedirs('src/ingestion', exist_ok=True)
with open('src/ingestion/ohlcv.py', 'w') as f:
    f.write('\
\\)" >> gen1.py && echo "    f.write(chr(10) + OHLCV
Data
Ingestion
Module + chr(10) + chr(10))" >> gen1.py && echo "    f.write(Supports
multiple
data
providers
with
failover: + chr(10))" >> gen1.py && echo "    f.write(Polygon.io
primary + chr(10))" >> gen1.py && echo "    f.write(Yahoo
Finance
fallback + chr(10))" >> gen1.py && echo "    f.write(Alpha
Vantage
fallback + chr(10))" >> gen1.py && echo "    f.write(\\\' + chr(10) + chr(10))
    f.write('import os' + chr(10))
    f.write('import asyncio' + chr(10))
    f.write('import aiohttp' + chr(10))
    f.write('import pandas as pd' + chr(10))
    f.write('import numpy as np' + chr(10))
    f.write('from datetime import datetime, timedelta' + chr(10))
    f.write('from typing import List, Dict, Optional, Any' + chr(10))
    f.write('from dataclasses import dataclass' + chr(10))
    f.write('from abc import ABC, abstractmethod' + chr(10))
    f.write('import logging' + chr(10) + chr(10))
    f.write('from src.utils.config import get_settings' + chr(10) + chr(10))
    f.write('logger = logging.getLogger(__name__)' + chr(10))
    f.write('settings = get_settings()' + chr(10) + chr(10))
