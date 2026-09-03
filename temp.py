import os; os.makedirs('src/utils', exist_ok=True)
open('src/utils/config.py', 'w').write(open('configs/base.yaml', 'r').read())
