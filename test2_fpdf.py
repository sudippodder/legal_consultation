import json
from fpdf import FPDF
pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'I', 9)
suggestion = 'A' * 1000
try:
    pdf.multi_cell(0, 5, suggestion)
    print('1000 worked')
except Exception as e:
    print('1000 failed:', type(e).__name__, e)

suggestion = 'A' * 3000
try:
    pdf.multi_cell(0, 5, suggestion)
    print('3000 worked')
except Exception as e:
    print('3000 failed:', type(e).__name__, e)
