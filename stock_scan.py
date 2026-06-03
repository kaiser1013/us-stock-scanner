import os
import smtplib
from email.message import EmailMessage

msg = EmailMessage()

msg["Subject"] = "US Stock Scanner Test"
msg["From"] = os.getenv("EMAIL_USER")
msg["To"] = os.getenv("EMAIL_TO")

msg.set_content("Hello from GitHub Actions!")

server = smtplib.SMTP_SSL(
    "smtp.gmail.com",
    465
)

server.login(
    os.getenv("EMAIL_USER"),
    os.getenv("EMAIL_PASSWORD")
)

server.send_message(msg)

server.quit()

print("Email sent successfully")
