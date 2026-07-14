from fpdf import FPDF
pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', 'I', 9)
suggestion = 'A' * 3000
try:
    pdf.multi_cell(0, 5, suggestion, wrapmode='CHAR')
    print('CHAR worked')
except Exception as e:
    print('CHAR failed:', type(e).__name__, e)
