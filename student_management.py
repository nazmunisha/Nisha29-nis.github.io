import re
from email_utils import send_student_login_email
from database import get_connection


# --------------------------------------------------
# Validate Email
# --------------------------------------------------
def valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


# --------------------------------------------------
# Generate Username
# --------------------------------------------------
def make_username(name):
    username = re.sub(r"[^a-z0-9]", "", str(name).lower())
    return username if username else "student"


# --------------------------------------------------
# Convert Uploaded Image to Bytes
# --------------------------------------------------
def image_bytes(uploaded_file):
    if uploaded_file:
        return uploaded_file.getvalue()
    return None


# --------------------------------------------------
# Create Student Login
# --------------------------------------------------
def create_student_login(cur, student_id, name):
    base = make_username(name)
    username = base
    count = 1

    while True:
        cur.execute(
            "SELECT user_id FROM users WHERE username=%s",
            (username,)
        )

        if not cur.fetchone():
            break

        count += 1
        username = f"{base}{count}"

    password = f"{username}{student_id}"

    cur.execute("""
        INSERT INTO users
        (username, password, role, student_id)
        VALUES (%s, %s, 'Student', %s)
    """, (
        username,
        password,
        int(student_id)
    ))

    return username, password


# --------------------------------------------------
# Add Student
# --------------------------------------------------
def add_student(
    roll_no,
    name,
    department,
    class_name,
    email,
    phone,
    photo_file
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        if not roll_no.strip():
            return False, "Roll Number is required.", None, None

        if not name.strip():
            return False, "Student Name is required.", None, None

        if email.strip() and not valid_email(email.strip()):
            return False, "Invalid email address.", None, None

        cur.execute(
            "SELECT student_id FROM students WHERE roll_no=%s",
            (roll_no.strip(),)
        )

        if cur.fetchone():
            return False, "Roll Number already exists.", None, None

        cur.execute("""
            INSERT INTO students
            (
                roll_no,
                name,
                department,
                class,
                email,
                phone,
                photo
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        """, (
            roll_no.strip(),
            name.strip(),
            department.strip(),
            class_name.strip(),
            email.strip(),
            phone.strip(),
            image_bytes(photo_file)
        ))

        student_id = cur.lastrowid

        username, password = create_student_login(
            cur,
            student_id,
            name.strip()
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        return False, f"Student could not be added: {e}", None, None

    finally:
        conn.close()

    if email.strip():
        try:
            print("Sending email to:", email.strip())

            send_student_login_email(
                email.strip(),
                name.strip(),
                username,
                password
            )

            print("Email sent successfully")
            message = f"Student added successfully. Login details emailed to {email.strip()}."

        except Exception as e:
            print("Email sending failed:", e)
            message = f"Student added successfully, but email failed: {e}"
    else:
        message = "Student added successfully. No email was provided."

    return True, message, username, password


# --------------------------------------------------
# Update Student
# --------------------------------------------------
def update_student(
    student_id,
    roll_no,
    name,
    department,
    class_name,
    email,
    phone,
    photo_file=None
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        if photo_file:
            cur.execute("""
                UPDATE students
                SET
                    roll_no=%s,
                    name=%s,
                    department=%s,
                    class=%s,
                    email=%s,
                    phone=%s,
                    photo=%s
                WHERE student_id=%s
            """, (
                roll_no,
                name,
                department,
                class_name,
                email,
                phone,
                image_bytes(photo_file),
                int(student_id)
            ))

        else:
            cur.execute("""
                UPDATE students
                SET
                    roll_no=%s,
                    name=%s,
                    department=%s,
                    class=%s,
                    email=%s,
                    phone=%s
                WHERE student_id=%s
            """, (
                roll_no,
                name,
                department,
                class_name,
                email,
                phone,
                int(student_id)
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# --------------------------------------------------
# Delete Student
# --------------------------------------------------
def delete_student(student_id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM attendance WHERE student_id=%s",
            (int(student_id),)
        )

        cur.execute(
            "DELETE FROM face_data WHERE student_id=%s",
            (int(student_id),)
        )

        cur.execute(
            "DELETE FROM users WHERE student_id=%s",
            (int(student_id),)
        )

        cur.execute(
            "DELETE FROM students WHERE student_id=%s",
            (int(student_id),)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
