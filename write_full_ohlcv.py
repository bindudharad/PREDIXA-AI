import os
os.makedirs('src/ingestion', exist_ok=True)
parts = []
parts.append(b'\
\\)" >> write_full_ohlcv.py && echo "parts.append(b\\nOHLCV
Data
Ingestion
Module\\n\\n)" >> write_full_ohlcv.py && echo "parts.append(bSupports
multiple
data
providers
with
failover:\\n)" >> write_full_ohlcv.py && echo "parts.append(bPolygon.io
primary\\n)" >> write_full_ohlcv.py && echo "parts.append(bYahoo
Finance
fallback\\n)" >> write_full_ohlcv.py && echo "parts.append(bAlpha
Vantage
fallback\\n)" >> write_full_ohlcv.py && echo "parts.append(b\\\\\n\\n')
parts.append(b'import os\\n')
parts.append(b'import asyncio\\n')
parts.append(b'import aiohttp\\n')
parts.append(b'import pandas as pd\\n')
parts.append(b'import numpy as np\\n')
parts.append(b'from datetime import datetime, timedelta\\n')
parts.append(b'from typing import List, Dict, Optional, Any\\n')
parts.append(b'from dataclasses import dataclass\\n')
parts.append(b'from abc import ABC, abstractmethod\\n')
parts.append(b'import logging\\n\\n')
parts.append(b'from src.utils.config import get_settings\\n\\n')
parts.append(b'logger = logging.getLogger(__name__)\\n')
parts.append(b'settings = get_settings()\\n\\n')
content = b''.join(parts)
with open('src/ingestion/ohlcv.py', 'wb') as f:
    f.write(content)
print('Part 1 written')
