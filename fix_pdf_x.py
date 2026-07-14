with open('utils/report_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'pdf.multi_cell' in line:
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + 'pdf.set_x(pdf.l_margin)\n')
    new_lines.append(line)

with open('utils/report_generator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Updated report_generator.py')
