from database import get_connection


def register_teacher(full_name, department, email, phone, username, password, confirm_password):
    if not full_name.strip() or not username.strip() or not password.strip():
        return False, "Name, username and password are required."

    if password != confirm_password:
        return False, "Passwords do not match."

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT teacher_id FROM teachers WHERE username=%s OR email=%s", (username.strip(), email.strip()))
    if cur.fetchone():
        conn.close()
        return False, "Username or email already exists."

    cur.execute("""
        INSERT INTO teachers
        (full_name, department, email, phone, username, password, status)
        VALUES (%s,%s,%s,%s,%s,%s,'Pending')
    """, (
        full_name.strip(),
        department.strip(),
        email.strip(),
        phone.strip(),
        username.strip(),
        password.strip()
    ))

    conn.commit()
    conn.close()

    return True, "Teacher registration submitted. Please wait for admin approval."


def get_pending_teachers():
    import pandas as pd

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT teacher_id, full_name, department, email, phone, username, status
        FROM teachers
        ORDER BY teacher_id DESC
    """)

    df = pd.DataFrame(cur.fetchall())
    conn.close()
    return df


def approve_teacher(teacher_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM teachers WHERE teacher_id=%s", (int(teacher_id),))
    teacher = cur.fetchone()

    if not teacher:
        conn.close()
        return False, "Teacher not found."

    cur.execute("""
        UPDATE teachers
        SET status='Approved'
        WHERE teacher_id=%s
    """, (int(teacher_id),))

    cur.execute("SELECT user_id FROM users WHERE username=%s", (teacher["username"],))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users (username, password, role, student_id)
            VALUES (%s, %s, 'Teacher', NULL)
        """, (teacher["username"], teacher["password"]))

    conn.commit()
    conn.close()

    return True, "Teacher approved and login created."


def reject_teacher(teacher_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE teachers
        SET status='Rejected'
        WHERE teacher_id=%s
    """, (int(teacher_id),))

    conn.commit()
    conn.close()

    return True, "Teacher rejected."