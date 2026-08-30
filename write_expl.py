import os
path = r'C:\\Programs\\PREDIXA AI\\docs\\16_EXPLAINABILITY.md'
content = open('explainability_content.txt', 'r', encoding='utf-8').read()
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('16_EXPLAINABILITY.md created')
