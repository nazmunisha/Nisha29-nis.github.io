import smtplib
from email.message import EmailMessage

SENDER_EMAIL = "saritasainildh@gmail.com"
APP_PASSWORD = "eznndripilsfrysp"

def send_student_login_email(student_email, student_name, username, password):
    msg = EmailMessage()
    msg["Subject"] = "Your Attendance System Login Details"
    msg["From"] = SENDER_EMAIL
    msg["To"] = student_email

    msg.set_content(f"""
Hello {student_name},

Your Attendance Management System account has been created.

Username: {username}
Password: {password}

Please keep these details safe.

Regards,
Attendance Management System
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)