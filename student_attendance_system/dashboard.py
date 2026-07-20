# ==========================================================
# Main Dashboard
# Purpose:
# Controls the complete application including UI,
# authentication, student management, teacher management,
# face recognition, attendance, reports and settings.
# ==========================================================

from pathlib import Path
from html import escape
import streamlit as st
import mysql.connector
import pandas as pd
import textwrap
import secrets
import string
import smtplib
from email.message import EmailMessage
from email_utils import SENDER_EMAIL, APP_PASSWORD
from password_utils import hash_password, check_password
from teacher_management import register_teacher, get_pending_teachers, approve_teacher, reject_teacher
from database import ensure_schema, load_data, get_connection
from auth import init_session, login_sidebar, logout
from student_management import add_student, update_student, delete_student
from face_recognition import (
    register_face,
    start_live_attendance_inside_dashboard
)

from attendance import get_student_attendance
from reports import monthly_attendance_report, student_summary



st.set_page_config(page_title="AMS Dashboard", page_icon="🎓", layout="wide")

# -----------------------------
# Language Selection
# -----------------------------
# Initialize language once
if "language" not in st.session_state or st.session_state.language not in ["English", "Te Reo Māori"]:
    st.session_state.language = "English"

languages = ["English", "Te Reo Māori"]

st.sidebar.selectbox(
    "🌐 Language / Reo",
    options=languages,
    index=languages.index(st.session_state.language),
    key="language"
)

LANG = {
    "English": {
        "app_title": "Attendance Management System",
        "hero_title": "Live Face Attendance System",
        "hero_subtitle": "OpenCV-based student attendance with live webcam recognition.",
        "login_info": "Please login from the left sidebar.",
        "logout": "Logout",
        "home": "Home",
        "add_student": "Add Student",
        "student_management": "Student Management",
        "teacher_approval": "Teacher Approval",
        "live_face_attendance": "Live Face Attendance",
        "attendance_records": "Attendance Records",
        "monthly_attendance": "Monthly Attendance",
        "student_dashboard": "Student Dashboard",
        "register_my_face": "Register My Face",
        "my_attendance": "My Attendance",
        "teacher_signup": "Teacher Sign Up",
        "full_name": "Full Name",
        "department": "Department",
        "email": "Email",
        "phone": "Phone",
        "choose_username": "Choose Username",
        "choose_password": "Choose Password",
        "confirm_password": "Confirm Password",
        "register_teacher": "Register as Teacher",
        "students": "Students",
        "total_students": "Total students",
        "attendance": "Attendance",
        "total_records": "Total records",
        "faces": "Faces",
        "registered_faces": "Registered faces",
        "face_scans": "Face Scans",
        "recognition_records": "Recognition records",
        "roll_number": "Roll Number",
        "student_name": "Student Name",
        "class_course": "Class / Course",
        "profile_photo": "Profile Photo",
        "add_student_submit": "✅ Add Student",
        "search_student": "Search student",
        "select_student": "Select Student",
        "save_update_face": "Save / Update Face",
        "capture_face": "Capture face for selected student",
        "recent_attendance": "Recent Attendance",
        "no_matching_student": "No matching student found.",
        "no_students": "No students found.",
        "teacher_approval_subtitle": "Approve or reject teacher sign-up requests",
        "no_teacher_requests": "No teacher registration requests.",
        "select_teacher": "Select Teacher",
        "approve_teacher": "✅ Approve Teacher",
        "reject_teacher": "❌ Reject Teacher",
        "start_live": "🎥 Start Live Attendance",
        "download_csv": "Download CSV",
        "no_attendance": "No attendance records.",
        "required_student": "Roll number and student name are required.",
        "register_my_face_subtitle": "Capture your own face for attendance",
        "own_face_info": "Only your own student account will be updated. You cannot register another student's face.",
        "capture_your_face": "Capture your face",
        "save_my_face": "Save / Update My Face",
        "only_own_attendance": "Only your own attendance records",
        "feature_face_recognition": "Face Recognition",
        "feature_face_recognition_desc": "Register student faces and mark attendance securely.",
        "feature_student_management": "Student Management",
        "feature_student_management_desc": "Add, edit, delete and manage student profiles.",
        "feature_reports": "Attendance Reports",
        "feature_reports_desc": "View records, monthly reports and attendance summaries.",
        "feature_email": "Email Notifications",
        "feature_email_desc": "Send login details, approvals and reset passwords by email.",
        "feature_teacher": "Teacher Approval",
        "feature_teacher_desc": "Teachers can register and wait for admin approval.",
        "feature_language": "English / Māori",
        "feature_language_desc": "Supports English and Te Reo Māori interface.",
        "system_features": "System Features",
        "system_highlights": "System Highlights",
        "built_with": "Built With",
        "footer_text": "Developed for MSE800 Professional Software Engineering",
        "version": "Version 1.0",
        "change_password": "Change Password",
        "current_password": "Current Password",
        "new_password": "New Password",
        "update_password": "Update Password",
        "password_changed": "Password changed successfully.",
        "current_password_wrong": "Current password is incorrect.",
        "passwords_not_match": "New password and confirm password do not match.",
        "password_required": "All password fields are required.",
        "forgot_password": "Forgot Password",
        "username_or_email": "Username or Email",
        "send_temp_password": "Send Temporary Password",
        "reset_sent": "Temporary password sent to your registered email.",
        "reset_not_found": "No student or teacher account found with this username/email.",
        "reset_no_email": "This account has no registered email address.",
        "reset_admin": "Admin password reset is not available by email. Please contact the system owner."
    },
    "Te Reo Māori": {
        "app_title": "Pūnaha Whakahaere Tae Mai",
        "hero_title": "Pūnaha Tae Mai Kanohi Ora",
        "hero_subtitle": "Tae mai ā-ākonga mā te kāmera ora me OpenCV.",
        "login_info": "Takiuru mai i te paetaha mauī.",
        "logout": "Takiputa",
        "home": "Kāinga",
        "add_student": "Tāpiri Ākonga",
        "student_management": "Whakahaere Ākonga",
        "teacher_approval": "Whakaaetanga Kaiako",
        "live_face_attendance": "Tae Mai Kanohi Ora",
        "attendance_records": "Ngā Rekoata Tae Mai",
        "monthly_attendance": "Tae Mai ā-Marama",
        "student_dashboard": "Papatohu Ākonga",
        "register_my_face": "Rēhita Taku Kanohi",
        "my_attendance": "Taku Tae Mai",
        "teacher_signup": "Rēhita Kaiako",
        "full_name": "Ingoa Katoa",
        "department": "Tari",
        "email": "Īmēra",
        "phone": "Waea",
        "choose_username": "Kōwhiri Ingoa Kaiwhakamahi",
        "choose_password": "Kōwhiri Kupuhipa",
        "confirm_password": "Whakaū Kupuhipa",
        "register_teacher": "Rēhita hei Kaiako",
        "students": "Ākonga",
        "total_students": "Tapeke ākonga",
        "attendance": "Tae Mai",
        "total_records": "Tapeke rekoata",
        "faces": "Kanohi",
        "registered_faces": "Kanohi kua rēhitatia",
        "face_scans": "Matawai Kanohi",
        "recognition_records": "Rekoata mōhiotanga",
        "roll_number": "Tau Rārangi",
        "student_name": "Ingoa Ākonga",
        "class_course": "Akomanga / Akoranga",
        "profile_photo": "Whakaahua Kōtaha",
        "add_student_submit": "✅ Tāpiri Ākonga",
        "search_student": "Rapu ākonga",
        "select_student": "Tīpako Ākonga",
        "save_update_face": "Tiaki / Whakahou Kanohi",
        "capture_face": "Hopukina te kanohi mō te ākonga kua tīpakohia",
        "recent_attendance": "Tae Mai Hou",
        "no_matching_student": "Kāore he ākonga e hāngai ana.",
        "no_students": "Kāore he ākonga.",
        "teacher_approval_subtitle": "Whakaae, whakakore rānei i ngā tono rēhita kaiako",
        "no_teacher_requests": "Kāore he tono rēhita kaiako.",
        "select_teacher": "Tīpako Kaiako",
        "approve_teacher": "✅ Whakaae Kaiako",
        "reject_teacher": "❌ Whakakore Kaiako",
        "start_live": "🎥 Tīmata Tae Mai Ora",
        "download_csv": "Tikiake CSV",
        "no_attendance": "Kāore he rekoata tae mai.",
        "required_student": "Me whakauru te tau rārangi me te ingoa ākonga.",
        "register_my_face_subtitle": "Hopukina tō ake kanohi mō te tae mai",
        "own_face_info": "Ka whakahoungia tō ake pūkete ākonga anake. Kāore e taea te rēhita i te kanohi o tētahi atu.",
        "capture_your_face": "Hopukina tō kanohi",
        "save_my_face": "Tiaki / Whakahou Taku Kanohi",
        "only_own_attendance": "Ngā rekoata tae mai mōu anake",
        "feature_face_recognition": "Mōhiotanga Kanohi",
        "feature_face_recognition_desc": "Rēhita kanohi ākonga me te tuhi tae mai haumaru.",
        "feature_student_management": "Whakahaere Ākonga",
        "feature_student_management_desc": "Tāpiri, whakatika, muku me te whakahaere kōtaha ākonga.",
        "feature_reports": "Pūrongo Tae Mai",
        "feature_reports_desc": "Tirohia ngā rekoata, ngā pūrongo ā-marama me ngā whakarāpopototanga.",
        "feature_email": "Whakamōhiotanga Īmēra",
        "feature_email_desc": "Tuku taipitopito takiuru, whakaaetanga me ngā kupuhipa rangitahi.",
        "feature_teacher": "Whakaaetanga Kaiako",
        "feature_teacher_desc": "Ka rēhita ngā kaiako, kātahi ka tatari mō te whakaaetanga kaiwhakahaere.",
        "feature_language": "Ingarihi / Māori",
        "feature_language_desc": "E tautoko ana i te atanga Ingarihi me Te Reo Māori.",
        "system_features": "Āhuatanga Pūnaha",
        "system_highlights": "Ngā Miramira Pūnaha",
        "built_with": "I Hangaia Ki",
        "footer_text": "I whakawhanaketia mō MSE800 Professional Software Engineering",
        "version": "Putanga 1.0",
        "change_password": "Huri Kupuhipa",
        "current_password": "Kupuhipa o Nāianei",
        "new_password": "Kupuhipa Hou",
        "update_password": "Whakahou Kupuhipa",
        "password_changed": "Kua angitū te huri kupuhipa.",
        "current_password_wrong": "Kei te hē te kupuhipa o nāianei.",
        "passwords_not_match": "Kāore ngā kupuhipa hou e ōrite.",
        "password_required": "Me whakakī ngā wāhanga kupuhipa katoa.",
        "forgot_password": "Kua Wareware te Kupuhipa",
        "username_or_email": "Ingoa Kaiwhakamahi, Īmēra rānei",
        "send_temp_password": "Tuku Kupuhipa Rangitahi",
        "reset_sent": "Kua tukuna te kupuhipa rangitahi ki tō īmēra kua rēhitatia.",
        "reset_not_found": "Kāore i kitea he pūkete ākonga, kaiako rānei mō tēnei ingoa/īmēra.",
        "reset_no_email": "Kāore he īmēra kua rēhitatia mō tēnei pūkete.",
        "reset_admin": "Kāore e wātea te tautuhi kupuhipa kaiwhakahaere mā te īmēra. Whakapā atu ki te kaipupuri pūnaha."
    }
}

T = LANG[st.session_state.language]


# ==========================================================
# Function: generate_roll_no()
# Purpose: Automatically generate the next student roll number.
# ==========================================================
def generate_roll_no():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(student_id) FROM students")
    last_id = cur.fetchone()[0]

    conn.close()

    if last_id is None:
        last_id = 0

    return f"2025{last_id + 1:04d}"




# -----------------------------
# Forgot Password Helpers
# -----------------------------
# ==========================================================
# Function: generate_temp_password()
# Purpose: Generate a secure temporary password.
# ==========================================================
def generate_temp_password():
    letters = "".join(secrets.choice(string.ascii_letters) for _ in range(4))
    digits = "".join(secrets.choice(string.digits) for _ in range(4))
    return "Temp@" + letters + digits


# ==========================================================
# Function: send_password_reset_email()
# Purpose: Send the temporary password to the user's email.
# ==========================================================
def send_password_reset_email(user_email, display_name, username, temp_password):
    msg = EmailMessage()
    msg["Subject"] = "Attendance System Password Reset"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email

    msg.set_content(f"""
Hello {display_name},

Your Attendance Management System password has been reset.

Username: {username}
Temporary Password: {temp_password}

Please log in using this temporary password and change it as soon as possible.

Regards,
Attendance Management System
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)


# ==========================================================
# Function: reset_user_password()
# Purpose: Reset the password for Student or Teacher accounts.
# ==========================================================
def reset_user_password(identifier):
    identifier = identifier.strip()

    if not identifier:
        return False, "Please enter username or email."

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT u.user_id, u.username, s.name AS display_name, s.email
            FROM users u
            JOIN students s ON u.student_id = s.student_id
            WHERE u.role='Student'
              AND (u.username=%s OR s.email=%s)
            LIMIT 1
        """, (identifier, identifier))

        account = cur.fetchone()

        if not account:
            cur.execute("""
                SELECT u.user_id, u.username, t.full_name AS display_name, t.email
                FROM users u
                JOIN teachers t ON u.username = t.username
                WHERE u.role='Teacher'
                  AND (u.username=%s OR t.email=%s)
                LIMIT 1
            """, (identifier, identifier))

            account = cur.fetchone()

        if not account:
            cur.execute("""
                SELECT user_id
                FROM users
                WHERE role='Admin' AND username=%s
                LIMIT 1
            """, (identifier,))

            admin = cur.fetchone()

            if admin:
                return False, T["reset_admin"]

        if not account:
            return False, T["reset_not_found"]

        if not account.get("email"):
            return False, T["reset_no_email"]

        temp_password = generate_temp_password()

        # Store only the hashed version of the temporary password.
        hashed_temp_password = hash_password(temp_password)

        cur.execute(
            "UPDATE users SET password=%s WHERE user_id=%s",
            (hashed_temp_password, account["user_id"])
        )

        conn.commit()

        send_password_reset_email(
            account["email"],
            account.get("display_name") or account["username"],
            account["username"],
            temp_password
        )

        return True, T["reset_sent"]

    except Exception as e:
        conn.rollback()
        return False, f"Password reset failed: {e}"

    finally:
        conn.close()


# -----------------------------
# Change Password Helper
# -----------------------------
# ==========================================================
# Function: change_user_password()
# Purpose: Allow users to change their password securely.
# ==========================================================
def change_user_password(user_id, current_password, new_password, confirm_password):
    if not current_password.strip() or not new_password.strip() or not confirm_password.strip():
        return False, T["password_required"]

    if new_password != confirm_password:
        return False, T["passwords_not_match"]

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            "SELECT password FROM users WHERE user_id=%s",
            (int(user_id),)
        )

        user = cur.fetchone()

        if not user:
            return False, "User not found."

        # Check typed current password against stored hash.
        if not check_password(current_password, user["password"]):
            return False, T["current_password_wrong"]

        # Store the new password as a secure bcrypt hash.
        hashed_new_password = hash_password(new_password)

        cur.execute(
            "UPDATE users SET password=%s WHERE user_id=%s",
            (hashed_new_password, int(user_id))
        )

        conn.commit()
        return True, T["password_changed"]

    except Exception as e:
        conn.rollback()
        return False, f"Password change failed: {e}"

    finally:
        conn.close()



# ==========================================================
# Function: load_css()
# Purpose: Load external CSS styling.
# ==========================================================
def load_css():
    css_file = Path(__file__).with_name("style.css")
    if css_file.exists():
        st.markdown(
            f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


load_css()

st.markdown("""
<style>
.user-photo{
    width:52px;
    height:52px;
    border-radius:50%;
    object-fit:cover;
    border:3px solid white;
    box-shadow:0 4px 12px rgba(0,0,0,.2);
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
.feature-grid{
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:16px;
    margin-top:14px;
}
.feature-card{
    background:#ffffff;
    border-radius:18px;
    padding:18px;
    box-shadow:0 10px 24px rgba(11,31,77,.07);
    border:1px solid #e8eef8;
    min-height:125px;
}
.feature-icon{
    width:46px;
    height:46px;
    border-radius:14px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:24px;
    background:#eef5ff;
    margin-bottom:10px;
}
.feature-card h3{
    margin:0 0 6px 0;
    color:#061b47;
    font-size:18px;
    font-weight:800;
}
.feature-card p{
    color:#66758e;
    font-size:14px;
    line-height:1.45;
    margin:0;
}
.section-title{
    margin-top:22px;
    margin-bottom:8px;
    font-size:22px;
    font-weight:900;
    color:#061b47;
}
.tech-row{
    display:grid;
    grid-template-columns:repeat(6, 1fr);
    gap:10px;
    margin-top:10px;
}
.tech-pill{
    background:#ffffff;
    border-radius:14px;
    padding:12px 10px;
    box-shadow:0 8px 18px rgba(11,31,77,.06);
    color:#061b47;
    font-weight:800;
    border:1px solid #e8eef8;
    text-align:center;
    font-size:14px;
}
.app-footer{
    margin-top:24px;
    padding:16px 22px;
    border-radius:16px;
    background:#ffffff;
    color:#061b47;
    border:1px solid #e8eef8;
    box-shadow:0 10px 24px rgba(11,31,77,.07);
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
}
.app-footer h3{
    margin:0;
    font-size:18px;
    font-weight:900;
}
.app-footer p{
    margin:3px 0;
    color:#66758e;
    font-size:13px;
}
.footer-badge{
    background:#0b3c88;
    color:white;
    padding:10px 14px;
    border-radius:999px;
    font-weight:800;
    white-space:nowrap;
}
@media(max-width: 1100px){
    .feature-grid{grid-template-columns:repeat(2, 1fr);}
    .tech-row{grid-template-columns:repeat(3, 1fr);}
}
@media(max-width: 700px){
    .feature-grid{grid-template-columns:1fr;}
    .tech-row{grid-template-columns:repeat(2, 1fr);}
    .app-footer{display:block;text-align:center;}
    .footer-badge{display:inline-block;margin-top:10px;}
}
</style>
""", unsafe_allow_html=True)


def safe(value):
    return escape(str(value)) if value is not None else ""


# ==========================================================
# Function: topbar()
# Purpose: Display application header and logged-in user.
# ==========================================================
def topbar(role="Guest", photo=None, name=None):
    import base64

    display_name = name if name else role

    if photo:
        img = base64.b64encode(photo).decode()
        avatar_html = f'<img src="data:image/png;base64,{img}" class="user-photo">'
    else:
        avatar_html = '<div class="avatar">👤</div>'

    html = f'<div class="topbar"><div class="topbar-left"><div class="topbar-title">{T["app_title"]}</div></div><div class="topbar-user">{avatar_html}<div><div class="user-name">{safe(display_name)}</div><div class="user-role">{safe(role)} Portal</div></div></div></div>'

    st.markdown(html, unsafe_allow_html=True)


# ==========================================================
# Function: hero()
# Purpose: Display welcome banner.
# ==========================================================
def hero():
    st.markdown(f"""
<div class="hero">
    <div>
        <h1>🎓 {T["hero_title"]}</h1>
        <p>{T["hero_subtitle"]}</p>
    </div>
    <div class="hero-badge">AMS<br>LIVE</div>
</div>
""", unsafe_allow_html=True)



def feature_card(icon, title, desc):
    st.markdown(f"""
<div class="feature-card">
    <div class="feature-icon">{safe(icon)}</div>
    <h3>{safe(title)}</h3>
    <p>{safe(desc)}</p>
</div>
""", unsafe_allow_html=True)


# ==========================================================
# Function: guest_homepage()
# Purpose: Display home page before login.
# ==========================================================
def guest_homepage(students_df=None, attendance_df=None, registered_face_ids=None, face_count=0):
    st.markdown(f'<div class="section-title">{safe(T["system_features"])}</div>', unsafe_allow_html=True)

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    feature_card("📷", T["feature_face_recognition"], T["feature_face_recognition_desc"])
    feature_card("👨‍🎓", T["feature_student_management"], T["feature_student_management_desc"])
    feature_card("📊", T["feature_reports"], T["feature_reports_desc"])
    feature_card("📧", T["feature_email"], T["feature_email_desc"])
    feature_card("👨‍🏫", T["feature_teacher"], T["feature_teacher_desc"])
    feature_card("🌏", T["feature_language"], T["feature_language_desc"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">{safe(T["built_with"])}</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="tech-row">
    <div class="tech-pill">🐍 Python</div>
    <div class="tech-pill">🌐 Streamlit</div>
    <div class="tech-pill">🗄 MySQL</div>
    <div class="tech-pill">📷 OpenCV</div>
    <div class="tech-pill">📧 SMTP</div>
    <div class="tech-pill">🌏 Bilingual</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="app-footer">
    <div>
        <h3>{safe(T["app_title"])}</h3>
        <p>{safe(T["footer_text"])}</p>
        <p>Developed by Sarita Dhiman and Nazmunisha Sheik Abdul Rasheed</p>
    </div>
    <div class="footer-badge">{safe(T["version"])}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# Function: page_header()
# Purpose: Display a standard page title.
# ==========================================================
def page_header(icon, title, subtitle, total_label=None, total_value=None):
    total_html = ""
    if total_label is not None:
        total_html = f"""
<div class="record-pill">
    <span>{safe(total_label)}</span>
    <b>{safe(total_value)}</b>
</div>
"""

    st.markdown(f"""
<div class="page-head">
    <div class="page-head-left">
        <div class="page-icon">{safe(icon)}</div>
        <div>
            <h1>{safe(title)}</h1>
            <p>{safe(subtitle)}</p>
        </div>
    </div>
    {total_html}
</div>
""", unsafe_allow_html=True)


def kpi_card(number, label, small, icon, color_class, bg_class):
    st.markdown(f"""
<div class="kpi-card {safe(color_class)}">
    <div class="kpi-icon {safe(bg_class)}">{safe(icon)}</div>
    <div class="kpi-number">{safe(number)}</div>
    <div class="kpi-label">{safe(label)}</div>
    <div class="kpi-small">{safe(small)}</div>
</div>
""", unsafe_allow_html=True)


def face_status(ok):
    return '<span class="status-present">Face Registered</span>' if ok else '<span class="status-absent">Face Not Registered</span>'


def show_photo(blob, width=150):
    if blob:
        st.image(blob, width=width)
    else:
        st.markdown('<div class="large-avatar">👤</div>',
                    unsafe_allow_html=True)


# ==========================================================
# Function: show_table()
# Purpose: Display data in table format.
# ==========================================================
def show_table(df, max_rows=25):
    if df.empty:
        st.info("No records found.")
        return
    view = df.head(max_rows).copy()
    if "photo" in view.columns:
        view = view.drop(columns=["photo"])
    st.dataframe(view, use_container_width=True, hide_index=True)


# ==========================================================
# Function: attendance_analytics_cards()
# Purpose: Display attendance analytics KPI cards.
# Shows total students, present today, absent today and
# today's attendance percentage.
# ==========================================================
def attendance_analytics_cards(students_df, attendance_df):
    today = pd.Timestamp.today().date()

    total_students = len(students_df) if students_df is not None else 0

    today_records = pd.DataFrame()

    if attendance_df is not None and not attendance_df.empty and "date" in attendance_df.columns:
        temp_df = attendance_df.copy()
        temp_df["date_only"] = pd.to_datetime(
            temp_df["date"], errors="coerce"
        ).dt.date

        today_records = temp_df[temp_df["date_only"] == today]

    present_today = 0
    absent_today = 0
    late_today = 0

    if not today_records.empty and "status" in today_records.columns:
        status_series = today_records["status"].astype(str).str.lower()
        present_today = int(status_series.eq("present").sum())
        absent_today = int(status_series.eq("absent").sum())
        late_today = int(status_series.eq("late").sum())

    attendance_percent = round(
        (present_today / total_students) * 100, 2
    ) if total_students else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(total_students, "Total Students",
                 "Registered students", "👥", "c-blue", "bg-blue")

    with c2:
        kpi_card(present_today, "Present Today",
                 "Marked present today", "✅", "c-green", "bg-green")

    with c3:
        kpi_card(absent_today, "Absent Today",
                 "Marked absent today", "🔴", "c-orange", "bg-orange")

    with c4:
        kpi_card(f"{attendance_percent}%", "Attendance Today",
                 "Present / total students", "📈", "c-purple", "bg-purple")

    return today_records


# ==========================================================
# Function: attendance_charts()
# Purpose: Display simple attendance charts for reports.
# ==========================================================
def attendance_charts(today_records, attendance_df):
    if today_records is not None and not today_records.empty and "status" in today_records.columns:
        st.markdown("### 📊 Today's Attendance Summary")
        today_summary = today_records["status"].astype(str).value_counts()
        st.bar_chart(today_summary)

    if attendance_df is not None and not attendance_df.empty and {"date", "status"}.issubset(attendance_df.columns):
        monthly_df = attendance_df.copy()
        monthly_df["month"] = pd.to_datetime(
            monthly_df["date"], errors="coerce"
        ).dt.to_period("M").astype(str)

        monthly_present = monthly_df[
            monthly_df["status"].astype(str).str.lower() == "present"
        ].groupby("month").size()

        if not monthly_present.empty:
            st.markdown("### 📈 Monthly Present Attendance Trend")
            st.line_chart(monthly_present)


try:
    ensure_schema()
except mysql.connector.Error as err:
    st.error(f"Database setup error: {err}")
    st.stop()

init_session()
login_sidebar()

if not st.session_state.logged_in:
    topbar("Guest")
    hero()
    st.info(T["login_info"])

    # Authentication support options
    with st.expander(f"🔑 {T['forgot_password']}"):
        with st.form("forgot_password_form"):
            reset_identifier = st.text_input(T["username_or_email"])
            reset_btn = st.form_submit_button(T["send_temp_password"])

        if reset_btn:
            ok, msg = reset_user_password(reset_identifier)

            if ok:
                st.success(msg)
            else:
                st.error(msg)

    # Teacher Sign Up should appear after Forgot Password.
    with st.expander(f"👨‍🏫 {T['teacher_signup']}"):
        with st.form("teacher_signup_form"):
            full_name = st.text_input(T["full_name"])
            department = st.text_input(T["department"])
            email = st.text_input(T["email"])
            phone = st.text_input(T["phone"])
            new_username = st.text_input(T["choose_username"])
            new_password = st.text_input(T["choose_password"], type="password")
            confirm_password = st.text_input(
                T["confirm_password"], type="password")

            register_btn = st.form_submit_button(T["register_teacher"])

        if register_btn:
            ok, msg = register_teacher(
                full_name,
                department,
                email,
                phone,
                new_username,
                new_password,
                confirm_password
            )

            if ok:
                st.success(msg)
            else:
                st.error(msg)

    guest_homepage()

    st.stop()

role = st.session_state.role
students_df, attendance_df, registered_face_ids = load_data()

face_count = 0
if not attendance_df.empty and "source" in attendance_df.columns:
    face_count = len(attendance_df[attendance_df["source"].astype(
        str).str.lower() == "facerecognition"])

with st.sidebar:
    st.markdown('<div class="sidebar-section">Navigation</div>',
                unsafe_allow_html=True)

    MENU_LABELS = {
        "Home": T["home"],
        "Add Student": T["add_student"],
        "Student Management": T["student_management"],
        "Teacher Approval": T["teacher_approval"],
        "Live Face Attendance": T["live_face_attendance"],
        "Attendance Records": T["attendance_records"],
        "Monthly Attendance": T["monthly_attendance"],
        "Student Dashboard": T["student_dashboard"],
        "Register My Face": T["register_my_face"],
        "My Attendance": T["my_attendance"],
        "Change Password": T["change_password"],
        "Logout": T["logout"]
    }

    if role == "Admin":
        menu = st.radio(
            "",
            [
                "Home",
                "Add Student",
                "Student Management",
                "Teacher Approval",
                "Live Face Attendance",
                "Attendance Records",
                "Monthly Attendance",
                "Change Password",
                "Logout"
            ],
            format_func=lambda x: MENU_LABELS.get(x, x),
            label_visibility="collapsed"
        )
    elif role == "Teacher":
        menu = st.radio(
            "",
            [
                "Home",
                "Student Management",
                "Live Face Attendance",
                "Attendance Records",
                "Monthly Attendance",
                "Change Password",
                "Logout"
            ],
            format_func=lambda x: MENU_LABELS.get(x, x),
            label_visibility="collapsed"
        )
    else:
        menu = st.radio(
            "",
            [
                "Student Dashboard",
                "My Attendance",
                "Change Password",
                "Logout"
            ],
            format_func=lambda x: MENU_LABELS.get(x, x),
            label_visibility="collapsed"
        )

    st.markdown('<div class="sidebar-art">📚🎓</div>', unsafe_allow_html=True)

# topbar(role)


conn = get_connection()
cur = conn.cursor(dictionary=True)

if role == "Student":

    cur.execute("""
        SELECT name, photo
        FROM students
        WHERE student_id=%s
    """, (st.session_state.student_id,))

    row = cur.fetchone()

    conn.close()

    if row:
        topbar(
            role="Student",
            photo=row["photo"],
            name=row["name"]
        )
    else:
        topbar(role)

else:
    conn.close()
    topbar(role)
if menu == "Home" and role in ["Admin", "Teacher"]:
    hero()

    st.markdown("### 📊 Today's Attendance Overview")
    attendance_analytics_cards(students_df, attendance_df)

    st.markdown("### 📌 System Overview")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(len(students_df), T["students"],
                 T["total_students"], "👥", "c-blue", "bg-blue")
    with c2:
        kpi_card(len(attendance_df), T["attendance"],
                 T["total_records"], "📋", "c-purple", "bg-purple")
    with c3:
        kpi_card(len(registered_face_ids),
                 T["faces"], T["registered_faces"], "📸", "c-green", "bg-green")
    with c4:
        kpi_card(face_count, T["face_scans"],
                 T["recognition_records"], "🤖", "c-orange", "bg-orange")

    summary = student_summary(attendance_df, students_df)
    show_table(summary, 25)


elif menu == "Add Student" and role == "Admin":
    page_header("➕", T["add_student"],
                "Add a student and automatically create login")

    with st.form("add_student"):
        col1, col2 = st.columns(2)

        with col1:
            roll_no = st.text_input(
                T["roll_number"], value=generate_roll_no(), disabled=True)
            name = st.text_input(T["student_name"])
            department = st.text_input(T["department"])
            photo = st.file_uploader(T["profile_photo"], type=[
                                     "jpg", "jpeg", "png"])

        with col2:
            class_name = st.text_input(T["class_course"])
            email = st.text_input(T["email"])
            phone = st.text_input(T["phone"])

        submit = st.form_submit_button(T["add_student_submit"])

    if submit:
        if not roll_no.strip() or not name.strip():
            st.error(T["required_student"])
        else:
            try:
                ok, msg, username, password = add_student(
                    roll_no, name, department, class_name, email, phone, photo)
                if ok:
                    st.success(f"✅ {msg}")
                    st.info(f"Student username: {username}")
                    st.info(f"Student password: {password}")
                else:
                    st.error(msg)
            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")


elif menu == "Student Management" and role in ["Admin", "Teacher"]:
    page_header("👥", T["student_management"],
                "View, edit, delete, register face", T["students"], len(students_df))

    if students_df.empty:
        st.info(T["no_students"])
    else:
        search = st.text_input(
            T["search_student"], placeholder="Name, roll no, department, email...")
        filtered = students_df.copy()

        if search:
            # Do not search BLOB/image columns such as photo.
            search_df = filtered.drop(columns=["photo"], errors="ignore")

            mask = search_df.astype(str).apply(
                lambda row: row.str.contains(search, case=False, na=False)
            ).any(axis=1)

            filtered = filtered[mask]

        if filtered.empty:
            st.warning(T["no_matching_student"])
        else:
            filtered = filtered.reset_index(drop=True)
            options = [
                f"{row.student_id} - {row.name} ({row.roll_no})" for _, row in filtered.iterrows()]
            selected = st.selectbox(T["select_student"], range(
                len(options)), format_func=lambda x: options[x])

            student = filtered.iloc[selected]
            student_id = int(student["student_id"])

            photo_col, info_col = st.columns([1, 3])

            with photo_col:
                show_photo(student.get("photo"), 150)

            with info_col:
                st.markdown(f"""
                <div class="panel">
                    <h2>{safe(student.get('name'))}</h2>
                    <p><b>Roll No:</b> {safe(student.get('roll_no'))}</p>
                    <p><b>Department:</b> {safe(student.get('department'))}</p>
                    <p><b>Course:</b> {safe(student.get('class'))}</p>
                    <p><b>Email:</b> {safe(student.get('email'))}</p>
                    <p><b>Phone:</b> {safe(student.get('phone'))}</p>
                    <p>{face_status(student_id in registered_face_ids)}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 📸 Register / Update Face")
            face_image = st.camera_input(
                T["capture_face"], key=f"face_{student_id}")

            if face_image:
                st.image(face_image, width=300, caption="Captured Face")
                if st.button(T["save_update_face"]):
                    ok, msg = register_face(student_id, face_image)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

            if role == "Admin":
                with st.expander("✏️ Edit Student"):
                    with st.form(f"edit_{student_id}"):
                        c1, c2 = st.columns(2)

                        with c1:
                            eroll = st.text_input(
                                T["roll_number"], value=str(student.get("roll_no", "")))
                            ename = st.text_input(
                                "Name", value=str(student.get("name", "")))
                            edepartment = st.text_input(
                                "Department", value=str(student.get("department", "")))
                            ephoto = st.file_uploader("Update Photo", type=[
                                                      "jpg", "jpeg", "png"], key=f"photo_{student_id}")

                        with c2:
                            eclass = st.text_input(
                                "Class", value=str(student.get("class", "")))
                            eemail = st.text_input(
                                "Email", value=str(student.get("email", "")))
                            ephone = st.text_input(
                                "Phone", value=str(student.get("phone", "")))

                        update = st.form_submit_button("Update Student")

                    if update:
                        try:
                            update_student(
                                student_id, eroll, ename, edepartment, eclass, eemail, ephone, ephoto)
                            st.success(
                                "✅ Student updated. Refresh page to see changes.")
                        except mysql.connector.Error as err:
                            st.error(f"Database error: {err}")

                with st.expander("🗑 Delete Student"):
                    st.warning(
                        "This will delete student, login, face data, and attendance records.")
                    confirm = st.text_input(
                        "Type DELETE to confirm", key=f"delete_{student_id}")

                    if st.button("Delete Student Permanently"):
                        if confirm != "DELETE":
                            st.error("Please type DELETE exactly.")
                        else:
                            try:
                                delete_student(student_id)
                                st.success("✅ Student deleted. Refresh page.")
                            except mysql.connector.Error as err:
                                st.error(f"Database error: {err}")

            st.markdown(f"### {T['recent_attendance']}")
            if not attendance_df.empty and "student_id" in attendance_df.columns:
                show_table(
                    attendance_df[attendance_df["student_id"] == student_id], 10)
            else:
                st.info("No attendance yet.")

elif menu == "Teacher Approval" and role == "Admin":
    page_header("👨‍🏫", T["teacher_approval"], T["teacher_approval_subtitle"])

    teachers_df = get_pending_teachers()

    if teachers_df.empty:
        st.info(T["no_teacher_requests"])
    else:
        st.dataframe(teachers_df, use_container_width=True, hide_index=True)

        teacher_options = [
            f"{row.teacher_id} - {row.full_name} ({row.username}) - {row.status}"
            for _, row in teachers_df.iterrows()
        ]

        selected_index = st.selectbox(
            T["select_teacher"],
            range(len(teacher_options)),
            format_func=lambda x: teacher_options[x]
        )

        selected_teacher_id = int(
            teachers_df.iloc[selected_index]["teacher_id"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button(T["approve_teacher"]):
                ok, msg = approve_teacher(selected_teacher_id)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        with col2:
            if st.button(T["reject_teacher"]):
                ok, msg = reject_teacher(selected_teacher_id)
                if ok:
                    st.warning(msg)
                else:
                    st.error(msg)
elif menu == "Live Face Attendance" and role in ["Admin", "Teacher"]:
    page_header("🎥", T["live_face_attendance"],
                "Live webcam attendance inside the dashboard")

    st.info("Click Start Live Attendance. The camera feed, student details, and attendance status will appear below for 60 seconds.")

    camera_col, detail_col = st.columns([2, 1])

    with camera_col:
        st.markdown("### 🎥 Live Camera")
        frame_placeholder = st.empty()

    with detail_col:
        st.markdown("### 👤 Recognition Details")
        status_placeholder = st.empty()
        detail_placeholder = st.empty()

    if st.button(T["start_live"]):
        ok, msg = start_live_attendance_inside_dashboard(
            frame_placeholder=frame_placeholder,
            status_placeholder=status_placeholder,
            detail_placeholder=detail_placeholder,
            duration=60
        )

        if ok:
            st.success(msg)
        else:
            st.error(msg)


elif menu == "Attendance Records" and role in ["Admin", "Teacher"]:
    page_header("📋", T["attendance_records"], "Attendance analytics and detailed records")

    # Dashboard analytics
    today_records = attendance_analytics_cards(students_df, attendance_df)

    attendance_charts(today_records, attendance_df)

    st.markdown("### 📄 Attendance Records")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input("Search records", placeholder="Search by student ID, status, source...")

    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Present", "Absent", "Late", "Excused"]
        )

    with col3:
        csv = attendance_df.to_csv(index=False).encode(
            "utf-8") if not attendance_df.empty else b""
        st.download_button(T["download_csv"], csv,
                           "attendance_records.csv", "text/csv")

    filtered = attendance_df.copy()

    if status_filter != "All" and not filtered.empty and "status" in filtered.columns:
        filtered = filtered[
            filtered["status"].astype(str).str.lower() == status_filter.lower()
        ]

    if search and not filtered.empty:
        search_df = filtered.drop(columns=["photo"], errors="ignore")

        mask = search_df.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False)
        ).any(axis=1)

        filtered = filtered[mask]

    show_table(filtered, 25)


elif menu == "Monthly Attendance" and role in ["Admin", "Teacher"]:
    page_header("📅", T["monthly_attendance"], "Monthly attendance percentage")
    report = monthly_attendance_report(attendance_df)
    if report.empty:
        st.info(T["no_attendance"])
    else:
        st.line_chart(report.set_index("month"))
        st.dataframe(report, use_container_width=True, hide_index=True)


elif menu == "Student Dashboard" and role == "Student":
    page_header("🎓", T["student_dashboard"],
                "Your personal profile and attendance")

    student_id = st.session_state.student_id

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cur.fetchone()
    conn.close()

    my_att = get_student_attendance(student_id)
    if my_att is None:
        my_att = pd.DataFrame()

    if not student:
        st.error("Student record not found.")
    else:
        present = (
            my_att["status"].astype(str).str.lower() == "present"
        ).sum() if not my_att.empty and "status" in my_att.columns else 0

        absent = (
            my_att["status"].astype(str).str.lower() == "absent"
        ).sum() if not my_att.empty and "status" in my_att.columns else 0

        total = len(my_att)
        percent = round(present / total * 100, 2) if total else 0

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            kpi_card(total, "Total Records",
                     "My attendance entries", "📋", "c-purple", "bg-purple")

        with c2:
            kpi_card(present, "Present",
                     "Present days", "✅", "c-green", "bg-green")

        with c3:
            kpi_card(absent, "Absent",
                     "Absent days", "🔴", "c-orange", "bg-orange")

        with c4:
            kpi_card(f"{percent}%", "Attendance %",
                     "Overall percentage", "📈", "c-blue", "bg-blue")

        pcol, icol = st.columns([1, 3])

        with pcol:
            show_photo(student.get("photo"), 150)

        with icol:
            st.markdown(f"""
            <div class="panel">
                <h2>{safe(student.get('name'))}</h2>
                <p><b>Roll No:</b> {safe(student.get('roll_no'))}</p>
                <p><b>Department:</b> {safe(student.get('department'))}</p>
                <p><b>Course:</b> {safe(student.get('class'))}</p>
                <p><b>Email:</b> {safe(student.get('email'))}</p>
            </div>
            """, unsafe_allow_html=True)





elif menu == "My Attendance" and role == "Student":
    page_header("📅", T["my_attendance"], T["only_own_attendance"])
    my_attendance = get_student_attendance(st.session_state.student_id)

    if my_attendance is None:
        my_attendance = pd.DataFrame()

    if my_attendance.empty:
        st.info(T["no_attendance"])
    else:
        csv = my_attendance.to_csv(index=False).encode("utf-8")
        st.download_button("Download My Attendance CSV", csv,
                           "my_attendance.csv", "text/csv")
        show_table(my_attendance, 25)



elif menu == "Change Password":
    page_header("🔐", T["change_password"], "Update your account password")

    with st.form("change_password_form"):
        current_password = st.text_input(T["current_password"], type="password")
        new_password = st.text_input(T["new_password"], type="password")
        confirm_password = st.text_input(T["confirm_password"], type="password")

        update_password_btn = st.form_submit_button(T["update_password"])

    if update_password_btn:
        ok, msg = change_user_password(
            st.session_state.user_id,
            current_password,
            new_password,
            confirm_password
        )

        if ok:
            st.success(msg)
        else:
            st.error(msg)


if menu == "Logout":
    logout()
