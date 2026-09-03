import os
os.makedirs('src/ingestion', exist_ok=True)
lines = []
lines.append('\
\\)" >> write_all.py && echo "lines.append(OHLCV
Data
Ingestion
Module)" >> write_all.py && echo "lines.append(')" >> write_all.py && echo "lines.append(Supports
multiple
data
providers
with
failover:)" >> write_all.py && echo "lines.append(Polygon.io
primary)" >> write_all.py && echo "lines.append(Yahoo
Finance
fallback)" >> write_all.py && echo "lines.append(Alpha
Vantage
fallback)" >> write_all.py && echo "lines.append(\\\')
lines.append('')
lines.append('import os')
lines.append('import asyncio')
lines.append('import aiohttp')
lines.append('import pandas as pd')
lines.append('import numpy as np')
lines.append('from datetime import datetime, timedelta')
lines.append('from typing import List, Dict, Optional, Any')
lines.append('from dataclasses import dataclass')
lines.append('from abc import ABC, abstractmethod')
lines.append('import logging')
lines.append('')
lines.append('from src.utils.config import get_settings')
lines.append('')
lines.append('logger = logging.getLogger(__name__)')
lines.append('settings = get_settings()')
lines.append('')
with open('src/ingestion/ohlcv.py', 'w') as f:
    f.write('\n'.join(lines))
