import pdfplumber

with pdfplumber.open(f"/pdf/Sra_green.pdf") as pdf:
    first_page = pdf.pages[4]
    print([x['text'] for x in first_page.chars])
    # breakpoint()