with open('utils/report_generator.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(', wrapmode=\"CHAR\"', '')

with open('utils/report_generator.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('wrapmode removed')
