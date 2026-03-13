from fpdf import FPDF
import datetime
from models.teachingevaluation import teachingevaluation
from models.service import service
from models.grants import grants
from models.professor import professor  # For scholarly outputs

class FARPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Faculty Activity Report', 0, 1, 'C')
        self.cell(0, 10, datetime.date.today().strftime('%B %d, %Y'), 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_far_pdf(professor_key, year=None):
    pdf = FARPDF()
    pdf.add_page()

    # Fetch data
    teachings = teachingevaluation().getByProfessor(professor_key)
    services = service().getByProfessor(professor_key)
    grants_list = grants().getByProfessor(professor_key)
    prof = professor()
    pubs = prof.getScholarlyOutputs(professor_key)  # List of dicts

    # Contents with counts (matching your PDF sample)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Contents', 0, 1)
    pdf.set_font('Arial', '', 10)
    toc = [
        ('1 JOURNAL ARTICLES', len([p for p in pubs if p['type'] == 'journal'])),
        ('2 REFEREED CONFERENCE PAPERS', len([p for p in pubs if p['type'] == 'refereed_conference'])),
        ('3 CONFERENCES', len([p for p in pubs if p['type'] == 'conference'])),
        ('4 SERVICE', len(services)),
        ('5 REVIEWING', 0),  # Add if reviews model added
        ('6 GRADUATE ADVISEES', 0),  # Add if thesis model added
        ('7 UNDERGRADUATE RESEARCH', 0),  # Add if undergrad research model added
        ('8 TEACHING', len(teachings)),
        ('9 PROPOSALS', len(grants_list)),  # Using grants as proxy; add proposals if separate
    ]
    for i, (title, count) in enumerate(toc, 1):
        pdf.cell(100, 10, title, 0, 0)
        pdf.cell(0, 10, str(count), 0, 1, 'R')
    pdf.add_page()

    # Section 1: JOURNAL ARTICLES (matching your PDF sample)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1 JOURNAL ARTICLES', 0, 1)
    pdf.set_font('Arial', '', 10)
    journals = [p for p in pubs if p['type'] == 'journal']
    for i, pub in enumerate(journals, 1):
        entry = f"{i}. {pub['authors']}. \"{pub['title']}\", {pub['venue']} {pub['year']}, p. {pub.get('pages', '')}. doi: {pub['doi']}."
        pdf.multi_cell(0, 10, entry)
    pdf.ln(5)

    # Section 4: SERVICE
    pdf.cell(0, 10, '4 SERVICE', 0, 1)
    headers = ['Year', 'Term', 'Type', 'Description', 'Hours']
    col_widths = [20, 30, 40, 80, 20]
    pdf.set_fill_color(200, 200, 200)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 10, h, 1, 0, 'C', True)
    pdf.ln()
    for svc in services:
        pdf.cell(col_widths[0], 10, str(svc['Calendar Year'] or ''), 1)
        pdf.cell(col_widths[1], 10, svc['Term'] or '', 1)
        pdf.cell(col_widths[2], 10, svc['Type'] or '', 1)
        pdf.multi_cell(col_widths[3], 10, svc['Description'] or '', 1)
        pdf.cell(col_widths[4], 10, str(svc['Hours/Semester'] or ''), 1)
        pdf.ln()
    pdf.ln(5)

    # Add more sections similarly (e.g., 8 TEACHING, 9 PROPOSALS)

    return pdf.output(dest='S').encode('latin1')