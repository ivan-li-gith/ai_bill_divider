import fitz  # PyMuPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def generate_pdf_breakdown(name, total, util, exp, sub):
    """Generates a PDF byte string in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    
    text = (
        f"Split Em - Expense Breakdown\n\n"
        f"Hello {name},\n"
        f"Here is your current outstanding balance breakdown:\n\n"
        f"Utilities: ${util:.2f}\n"
        f"One-Off Expenses: ${exp:.2f}\n"
        f"Subscriptions: ${sub:.2f}\n\n"
        f"Total Owed: ${total:.2f}"
    )
    
    page.insert_text(fitz.Point(50, 50), text, fontsize=12, fontname="helv")
    return doc.write()

def send_email_with_pdf(to_email, name, pdf_bytes):
    """Sends an email with the PyMuPDF generated attachment."""
    sender_email = os.environ.get("SENDER_EMAIL") 
    sender_password = os.environ.get("SENDER_PASSWORD") 
    
    msg = MIMEMultipart()
    msg['Subject'] = "Your Split Em Balance Breakdown"
    msg['From'] = sender_email
    msg['To'] = to_email

    body = MIMEText(f"Hi {name},\n\nPlease find attached your expense breakdown PDF.\n\nCheers,\nSplit Em")
    msg.attach(body)

    part = MIMEApplication(pdf_bytes, Name="Balance_Breakdown.pdf")
    part['Content-Disposition'] = 'attachment; filename="Balance_Breakdown.pdf"'
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.set_debuglevel(1)
        server.login(sender_email, sender_password)
        server.send_message(msg)