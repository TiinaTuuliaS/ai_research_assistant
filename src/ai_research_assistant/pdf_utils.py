from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import os

def create_pdf(report_text, filename):
    os.makedirs("reports", exist_ok=True)

    filepath = f"reports/{filename}"

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()

    content = []

    # 🔥 pilkotaan teksti riveihin
    for line in report_text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)

    return filepath