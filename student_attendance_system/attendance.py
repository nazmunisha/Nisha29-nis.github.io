"""
==========================================================
Attendance Management System
File: attendance.py

Purpose:
This file handles:
1. Face recognition attendance.
2. Manual attendance by Admin/Teacher.
3. Marking unscanned students as Absent.
4. Student attendance history.
5. All attendance records.

==========================================================
"""

from database import get_connection


# ==========================================================
# Function: mark_attendance()
# Purpose : Mark attendance using face recognition.
# ==========================================================
def mark_attendance(student_id):
    student_id = int(student_id)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT name FROM students WHERE student_id=%s",
        (student_id,)
    )

    student = cur.fetchone()
    student_name = student["name"] if student else f"Student {student_id}"

    cur.execute("""
        SELECT attendance_id
        FROM attendance
        WHERE student_id=%s AND date=CURDATE()
        LIMIT 1
    """, (student_id,))

    already = cur.fetchone()

    if already:
        conn.close()
        return False, student_name, "Attendance Already Marked Today"

    cur.execute("""
        INSERT INTO attendance
        (student_id, date, time, status, source, device_type)
        VALUES
        (%s, CURDATE(), CURTIME(), 'Present', 'FaceRecognition', 'Laptop')
    """, (student_id,))

    conn.commit()
    conn.close()

    return True, student_name, "Attendance Marked Successfully"


# ==========================================================
# Function: mark_manual_attendance()
# Purpose : Admin/Teacher can manually mark or update attendance.
# ==========================================================
def mark_manual_attendance(student_id, status, device_type="TeacherDashboard"):
    student_id = int(student_id)
    status = str(status).strip()

    allowed_status = ["Present", "Absent", "Late", "Excused"]

    if status not in allowed_status:
        return False, "Invalid attendance status."

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            "SELECT name FROM students WHERE student_id=%s",
            (student_id,)
        )

        student = cur.fetchone()
        student_name = student["name"] if student else f"Student {student_id}"

        cur.execute("""
            SELECT attendance_id
            FROM attendance
            WHERE student_id=%s AND date=CURDATE()
            LIMIT 1
        """, (student_id,))

        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE attendance
                SET time=CURTIME(),
                    status=%s,
                    source='Manual',
                    device_type=%s
                WHERE attendance_id=%s
            """, (
                status,
                device_type,
                existing["attendance_id"]
            ))

            msg = f"{student_name}'s attendance updated to {status}."

        else:
            cur.execute("""
                INSERT INTO attendance
                (student_id, date, time, status, source, device_type)
                VALUES
                (%s, CURDATE(), CURTIME(), %s, 'Manual', %s)
            """, (
                student_id,
                status,
                device_type
            ))

            msg = f"{student_name}'s attendance marked as {status}."

        conn.commit()
        return True, msg

    except Exception as e:
        conn.rollback()
        return False, f"Manual attendance failed: {e}"

    finally:
        conn.close()


# ==========================================================
# Function: mark_absent_for_unmarked_today()
# Purpose : End session and mark all unmarked students Absent.
# ==========================================================
def mark_absent_for_unmarked_today():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT student_id
            FROM students
            WHERE student_id NOT IN (
                SELECT student_id
                FROM attendance
                WHERE date=CURDATE()
            )
        """)

        unmarked_students = cur.fetchall()

        count = 0

        for student in unmarked_students:
            cur.execute("""
                INSERT INTO attendance
                (student_id, date, time, status, source, device_type)
                VALUES
                (%s, CURDATE(), CURTIME(), 'Absent', 'Manual', 'TeacherDashboard')
            """, (int(student["student_id"]),))

            count += 1

        conn.commit()

        return True, "Absent records created successfully.", count

    except Exception as e:
        conn.rollback()
        return False, f"Could not mark absent records: {e}", 0

    finally:
        conn.close()


# ==========================================================
# Function: get_student_attendance()
# Purpose : Return attendance history of one student.
# ==========================================================
def get_student_attendance(student_id):
    import pandas as pd

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT attendance_id, student_id, date, time, status, source, device_type
        FROM attendance
        WHERE student_id=%s
        ORDER BY date DESC, time DESC
    """, (int(student_id),))

    rows = cur.fetchall()
    conn.close()

    return pd.DataFrame(rows)


# ==========================================================
# Function: get_all_attendance()
# Purpose : Return all attendance records.
# ==========================================================
def get_all_attendance():
    import pandas as pd

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            a.attendance_id,
            a.student_id,
            s.roll_no,
            s.name,
            s.department,
            s.class,
            a.date,
            a.time,
            a.status,
            a.source,
            a.device_type
        FROM attendance a
        JOIN students s
        ON a.student_id = s.student_id
        ORDER BY a.date DESC, a.time DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return pd.DataFrame(rows)
