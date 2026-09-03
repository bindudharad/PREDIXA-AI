import os; os.makedirs('src/ingestion', exist_ok=True)
with open('src/ingestion/ohlcv.py', 'wb') as f:
    f.write(b'test')
