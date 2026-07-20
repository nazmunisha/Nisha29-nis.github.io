# ==========================================================
# Purpose:
# This file contains all email-related functions used in the
# Attendance Management System.
#
# Features:
# • Send student login details
# • Send teacher approval email
# • Send password reset email
#
# Technology Used:
# • Python smtplib
# • EmailMessage
# • Gmail SMTP with SSL
# ==========================================================

# Import SMTP library for sending emails
import smtplib

# Import EmailMessage class to create email content
from email.message import EmailMessage


# ==========================================================
# Gmail Account Configuration
# ==========================================================

# Sender Gmail address
SENDER_EMAIL = "testsarita9@gmail.com"

# Gmail App Password
# (Generated from Google Account → Security → App Passwords)
APP_PASSWORD = "ywgncrceisopbjwb"


# ==========================================================
# Function: send_student_login_email()
# Purpose:
# Send login credentials to a newly registered student.
#
# Parameters:
# student_email - Student's registered email address
# student_name  - Student's full name
# username      - Student login username
# password      - Student login password
# ==========================================================
def send_student_login_email(student_email, student_name, username, password):

    # Create email object
    msg = EmailMessage()

    # Email subject
    msg["Subject"] = "Your Attendance System Login Details"

    # Sender email
    msg["From"] = SENDER_EMAIL

    # Receiver email
    msg["To"] = student_email

    # Email body
    msg.set_content(f"""
Hello {student_name},

Your Attendance Management System account has been created.

Username: {username}
Password: {password}

Please keep these details safe.

Regards,
Attendance Management System
""")

    # Connect securely to Gmail SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        # Login using Gmail App Password
        smtp.login(SENDER_EMAIL, APP_PASSWORD)

        # Send email
        smtp.send_message(msg)


# ==========================================================
# Function: send_teacher_approval_email()
# Purpose:
# Notify a teacher that their registration request
# has been approved by the administrator.
#
# Parameters:
# teacher_email - Teacher's email
# teacher_name  - Teacher's full name
# username      - Teacher login username
# password      - Teacher login password
# ==========================================================
def send_teacher_approval_email(
    teacher_email,
    teacher_name,
    username
):
    """
    Notify a teacher that their account has been approved.

    Security note:
    The teacher's password is stored only as a bcrypt hash,
    so it cannot and should not be included in the email.
    The teacher should use the password chosen during signup.
    """

    msg = EmailMessage()
    msg["Subject"] = "Teacher Account Approved"
    msg["From"] = SENDER_EMAIL
    msg["To"] = teacher_email

    msg.set_content(f"""
Hello {teacher_name},

Congratulations!

Your teacher registration request has been approved.

You can now log in to the Attendance Management System.

Username: {username}
Password: Use the password you selected during registration.

Regards,
Attendance Management System
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)


# ==========================================================
# Function: send_password_reset_email()
# Purpose:
# Send a temporary password to the user when they
# request a password reset.
#
# Parameters:
# user_email    - Registered email address
# username      - User login username
# temp_password - Newly generated temporary password
# ==========================================================
def send_password_reset_email(
    user_email,
    username,
    temp_password
):

    # Create email object
    msg = EmailMessage()

    # Email subject
    msg["Subject"] = "Attendance System Password Reset"

    # Sender email
    msg["From"] = SENDER_EMAIL

    # Receiver email
    msg["To"] = user_email

    # Email body
    msg.set_content(f"""
Hello,

Your Attendance Management System password has been reset.

Username: {username}

Temporary Password:
{temp_password}

Please log in using this temporary password and change it immediately.

Regards,
Attendance Management System
""")

    # Connect securely to Gmail SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        # Login using Gmail App Password
        smtp.login(SENDER_EMAIL, APP_PASSWORD)

        # Send email
        smtp.send_message(msg)