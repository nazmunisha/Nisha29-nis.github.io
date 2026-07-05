from pathlib import Path
from html import escape
import streamlit as st
import mysql.connector
import pandas as pd
import textwrap
from teacher_management import register_teacher, get_pending_teachers, approve_teacher, reject_teacher
from database import ensure_schema, load_data, get_connection
from auth import init_session, login_sidebar, logout
from student_management import add_student, update_student, delete_student
from face_recognition import register_face, start_live_attendance
from attendance import get_student_attendance
from reports import monthly_attendance_report, student_summary


st.set_page_config(page_title="AMS Dashboard", page_icon="🎓", layout="wide")

# -----------------------------
# Language Selection
# -----------------------------
if "language" not in st.session_state:
    st.session_state.language = "English"

st.session_state.language = st.sidebar.selectbox(
    "🌐 Language / Reo",
    ["English", "Te Reo Māori"],
    index=0 if st.session_state.language == "English" else 1
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
        "only_own_attendance": "Only your own attendance records"
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
        "only_own_attendance": "Ngā rekoata tae mai mōu anake"
    }
}

T = LANG[st.session_state.language]




def generate_roll_no():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(student_id) FROM students")
    last_id = cur.fetchone()[0]

    conn.close()

    if last_id is None:
        last_id = 0

    return f"2025{last_id + 1:04d}"
def load_css():
    css_file = Path(__file__).with_name("style.css")
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


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



def safe(value):
    return escape(str(value)) if value is not None else ""
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
        st.markdown('<div class="large-avatar">👤</div>', unsafe_allow_html=True)


def show_table(df, max_rows=25):
    if df.empty:
        st.info("No records found.")
        return
    view = df.head(max_rows).copy()
    if "photo" in view.columns:
        view = view.drop(columns=["photo"])
    st.dataframe(view, use_container_width=True, hide_index=True)


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

    with st.expander(f"👨‍🏫 {T['teacher_signup']}"):
        with st.form("teacher_signup_form"):
            full_name = st.text_input(T["full_name"])
            department = st.text_input(T["department"])
            email = st.text_input(T["email"])
            phone = st.text_input(T["phone"])
            new_username = st.text_input(T["choose_username"])
            new_password = st.text_input(T["choose_password"], type="password")
            confirm_password = st.text_input(T["confirm_password"], type="password")

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

    st.stop()

role = st.session_state.role
students_df, attendance_df, registered_face_ids = load_data()

face_count = 0
if not attendance_df.empty and "source" in attendance_df.columns:
    face_count = len(attendance_df[attendance_df["source"].astype(str).str.lower() == "facerecognition"])

with st.sidebar:
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)

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
                "Register My Face",
                "My Attendance",
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
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(len(students_df), T["students"], T["total_students"], "👥", "c-blue", "bg-blue")
    with c2:
        kpi_card(len(attendance_df), T["attendance"], T["total_records"], "📋", "c-purple", "bg-purple")
    with c3:
        kpi_card(len(registered_face_ids), T["faces"], T["registered_faces"], "📸", "c-green", "bg-green")
    with c4:
        kpi_card(face_count, T["face_scans"], T["recognition_records"], "🤖", "c-orange", "bg-orange")

    summary = student_summary(attendance_df, students_df)
    show_table(summary, 25)


elif menu == "Add Student" and role == "Admin":
    page_header("➕", T["add_student"], "Add a student and automatically create login")

    with st.form("add_student"):
        col1, col2 = st.columns(2)

        with col1:
            roll_no = st.text_input(T["roll_number"],value=generate_roll_no(), disabled=True)
            name = st.text_input(T["student_name"])
            department = st.text_input(T["department"])
            photo = st.file_uploader(T["profile_photo"], type=["jpg", "jpeg", "png"])

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
                ok, msg, username, password = add_student(roll_no, name, department, class_name, email, phone, photo)
                if ok:
                    st.success(f"✅ {msg}")
                    st.info(f"Student username: {username}")
                    st.info(f"Student password: {password}")
                else:
                    st.error(msg)
            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")


elif menu == "Student Management" and role in ["Admin", "Teacher"]:
    page_header("👥", T["student_management"], "View, edit, delete, register face", T["students"], len(students_df))

    if students_df.empty:
        st.info(T["no_students"])
    else:
        search = st.text_input(T["search_student"], placeholder="Name, roll no, department, email...")
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
            options = [f"{row.student_id} - {row.name} ({row.roll_no})" for _, row in filtered.iterrows()]
            selected = st.selectbox(T["select_student"], range(len(options)), format_func=lambda x: options[x])

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
            face_image = st.camera_input(T["capture_face"], key=f"face_{student_id}")

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
                            eroll = st.text_input(T["roll_number"], value=str(student.get("roll_no", "")))
                            ename = st.text_input("Name", value=str(student.get("name", "")))
                            edepartment = st.text_input("Department", value=str(student.get("department", "")))
                            ephoto = st.file_uploader("Update Photo", type=["jpg", "jpeg", "png"], key=f"photo_{student_id}")

                        with c2:
                            eclass = st.text_input("Class", value=str(student.get("class", "")))
                            eemail = st.text_input("Email", value=str(student.get("email", "")))
                            ephone = st.text_input("Phone", value=str(student.get("phone", "")))

                        update = st.form_submit_button("Update Student")

                    if update:
                        try:
                            update_student(student_id, eroll, ename, edepartment, eclass, eemail, ephone, ephoto)
                            st.success("✅ Student updated. Refresh page to see changes.")
                        except mysql.connector.Error as err:
                            st.error(f"Database error: {err}")

                with st.expander("🗑 Delete Student"):
                    st.warning("This will delete student, login, face data, and attendance records.")
                    confirm = st.text_input("Type DELETE to confirm", key=f"delete_{student_id}")

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
                show_table(attendance_df[attendance_df["student_id"] == student_id], 10)
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

        selected_teacher_id = int(teachers_df.iloc[selected_index]["teacher_id"])

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
    page_header("🎥", T["live_face_attendance"], "Camera opens inside dashboard")

    frame_placeholder = st.empty()
    status_placeholder = st.empty()

    if st.button(T["start_live"]):
        try:
            ok, msg = start_live_attendance(
                frame_placeholder=frame_placeholder,
                status_placeholder=status_placeholder,
                duration=60
            )
        except TypeError:
            ok, msg = start_live_attendance()

        if ok:
            st.success(msg)
        else:
            st.error(msg)


elif menu == "Attendance Records" and role in ["Admin", "Teacher"]:
    page_header("📋", T["attendance_records"], "View all attendance records", T["total_records"], len(attendance_df))

    col1, col2 = st.columns([3, 1])

    with col1:
        search = st.text_input("Search records", placeholder="Search...")

    with col2:
        csv = attendance_df.to_csv(index=False).encode("utf-8") if not attendance_df.empty else b""
        st.download_button(T["download_csv"], csv, "attendance_records.csv", "text/csv")

    filtered = attendance_df.copy()

    if search and not filtered.empty:
        # Do not search BLOB/image columns such as photo.
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
    page_header("🎓", T["student_dashboard"], "Your personal profile and attendance")
    student_id = st.session_state.student_id

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cur.fetchone()
    conn.close()

    my_att = get_student_attendance(student_id)

    if not student:
        st.error("Student record not found.")
    else:
        present = (my_att["status"].astype(str).str.lower() == "present").sum() if not my_att.empty and "status" in my_att.columns else 0
        total = len(my_att)
        percent = round(present / total * 100, 2) if total else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card(f"{percent}%", "Attendance", "Overall attendance", "📈", "c-blue", "bg-blue")
        with c2:
            kpi_card(present, "Present", "Present days", "✅", "c-green", "bg-green")
        with c3:
            kpi_card(total - present, "Absent/Late", "Other days", "🔴", "c-orange", "bg-orange")

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


elif menu == "Register My Face" and role == "Student":
    page_header("📸", T["register_my_face"], T["register_my_face_subtitle"])

    st.info("Only your own student account will be updated. You cannot register another student's face.")

    face_image = st.camera_input(T["capture_your_face"])

    if face_image:
        st.image(face_image, width=300, caption="Captured Face")

        if st.button(T["save_my_face"]):
            ok, msg = register_face(st.session_state.student_id, face_image)

            if ok:
                st.success(msg)
            else:
                st.error(msg)


elif menu == "My Attendance" and role == "Student":
    page_header("📅", T["my_attendance"], T["only_own_attendance"])
    my_attendance = get_student_attendance(st.session_state.student_id)

    if my_attendance.empty:
        st.info(T["no_attendance"])
    else:
        csv = my_attendance.to_csv(index=False).encode("utf-8")
        st.download_button("Download My Attendance CSV", csv, "my_attendance.csv", "text/csv")
        show_table(my_attendance, 25)


if menu == "Logout":
    logout()
