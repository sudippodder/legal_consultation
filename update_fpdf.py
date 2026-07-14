import re

with open('utils/report_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We only want to replace instances that do NOT already have wrapmode="CHAR"
# pdf.multi_cell(0, 5, _safe_text(f"  Suggestion: {suggestion}"))
# pdf.multi_cell(0, 5, _safe_text(f"  {explanation}"))
# pdf.multi_cell(0, 6, _safe_text(f"{i}. {rec}"))
# pdf.multi_cell(0, 6, _safe_text(summary))
# pdf.multi_cell(0, 6, _safe_text(f"  * {point}"))
# pdf.multi_cell(0, 6, _safe_text(line))
# pdf.multi_cell(0, 6, _safe_text(f"  * {item}"))

import ast

def replace_calls(code_str):
    # simpler approach using regex that works over newlines
    # Find all pdf.multi_cell(..., _safe_text(...)) and add wrapmode='CHAR'
    
    lines = code_str.split('\n')
    new_lines = []
    for line in lines:
        if 'pdf.multi_cell(' in line and '_safe_text(' in line and 'wrapmode' not in line:
            # simple replacement for the most common ones which end with '))'
            if line.rstrip().endswith('))'):
                line = line.replace('))', '), wrapmode="CHAR")')
        new_lines.append(line)
    return '\n'.join(new_lines)

new_content = replace_calls(content)

with open('utils/report_generator.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated report_generator.py successfully.')
