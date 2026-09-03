import os
os.makedirs('src/ingestion', exist_ok=True)
with open('src/ingestion/ohlcv.py', 'a') as f:
    f.write('@dataclass' + chr(10))
    f.write('class OHLCVBar:' + chr(10))
    f.write('    \
\\Single
OHLCV
bar\\\' + chr(10))
    f.write('    symbol: str' + chr(10))
    f.write('    timestamp: pd.Timestamp' + chr(10))
    f.write('    open: float' + chr(10))
    f.write('    high: float' + chr(10))
    f.write('    low: float' + chr(10))
    f.write('    close: float' + chr(10))
    f.write('    volume: int' + chr(10))
    f.write('    vwap = None' + chr(10))
    f.write('    transactions = None' + chr(10) + chr(10))
