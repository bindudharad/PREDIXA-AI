import os
os.makedirs('src/ingestion', exist_ok=True)
with open('src/ingestion/ohlcv.py', 'w') as out:
    out.write('test content')
