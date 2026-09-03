import os
os.makedirs('src/ingestion', exist_ok=True)
with open('src/ingestion/ohlcv.py', 'wb') as f:
    f.write(b'\
\\\\nOHLCV
Data
Ingestion
Module\\n\\nSupports
multiple
data
providers
with
failover:\\nPolygon.io
primary\\nYahoo
Finance
fallback\\nAlpha
Vantage
fallback\\n\\\\\n\\n')
    f.write(b'import os\\nimport asyncio\\nimport aiohttp\\nimport pandas as pd\\nimport numpy as np\\n')
    f.write(b'from datetime import datetime, timedelta\\nfrom typing import List, Dict, Optional, Any\\n')
    f.write(b'from dataclasses import dataclass\\nfrom abc import ABC, abstractmethod\\nimport logging\\n\\n')
    f.write(b'from src.utils.config import get_settings\\n\\n')
    f.write(b'logger = logging.getLogger(__name__)\\nsettings = get_settings()\\n\\n')
print('Part 1 done')
