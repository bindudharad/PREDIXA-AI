import os; os.makedirs('src/utils', exist_ok=True)
with open('src/utils/config.py', 'w') as f: f.write(open('config_template.py').read())
