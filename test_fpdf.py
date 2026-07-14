import json
from fpdf import FPDF
def _safe_text(text: str) -> str:
    if not text: return ''
    return text.replace('\t', '    ').replace('\n', ' ')

pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'I', 9)
suggestion = '  Suggestion: ' + 'A' * 300
try:
    pdf.multi_cell(0, 5, _safe_text(suggestion))
    print('Long word worked')
except Exception as e:
    print('Long word failed:', type(e).__name__, e)

pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'I', 9)
suggestion = '  Suggestion: ' + 'A' * 100 + '\u00a0' + 'B' * 100
try:
    pdf.multi_cell(0, 5, _safe_text(suggestion))
    print('Long word with nbs worked')
except Exception as e:
    print('Long word with nbs failed:', type(e).__name__, e)
