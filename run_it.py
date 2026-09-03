f = open('src/ingestion/ohlcv.py', 'wb')
f.write(b'\
\\)" >> run_it.py && echo "f.write(b\\nOHLCV
Data
Ingestion
Module\\n\\n)" >> run_it.py && echo "f.write(bSupports
multiple
data
providers
with
failover:\\n)" >> run_it.py && echo "f.write(bPolygon.io
primary\\n)" >> run_it.py && echo "f.write(bYahoo
Finance
fallback\\n)" >> run_it.py && echo "f.write(bAlpha
Vantage
fallback\\n)" >> run_it.py && echo "f.write(b\\\\\n\\n')
f.write(b'import os\\n')
f.write(b'import asyncio\\n')
f.write(b'import aiohttp\\n')
f.write(b'import pandas as pd\\n')
f.write(b'import numpy as np\\n')
f.write(b'from datetime import datetime, timedelta\\n')
f.write(b'from typing import List, Dict, Optional, Any\\n')
f.write(b'from dataclasses import dataclass\\n')
f.write(b'from abc import ABC, abstractmethod\\n')
f.write(b'import logging\\n\\n')
f.write(b'from src.utils.config import get_settings\\n\\n')
f.write(b'logger = logging.getLogger(__name__)\\n')
f.write(b'settings = get_settings()\\n\\n')
f.close()
print('Part 1 done')
