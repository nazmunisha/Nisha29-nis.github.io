# ==========================================================#
# Purpose:
# This module manages all teacher-related operations:
# - Teacher registration
# - Viewing teacher registration requests
# - Approving teachers
# - Rejecting teachers
# - Creating teacher login accounts
# - Sending teacher approval emails
#
# Technologies Used:
# - Python
# - MySQL
# - Pandas
# - Gmail SMTP through email_utils.py
# ==========================================================

# Import database connection function
from database import get_connection

# Import email function used when admin approves a teacher
from email_utils import send_teacher_approval_email
from password_utils import hash_password


# ==========================================================
# Function: register_teacher()
#
# Purpose:
# Register a teacher request in the system.
#
# Important:
# A teacher is NOT allowed to log in immediately.
# Their status is first saved as "Pending".
# Admin must approve the teacher before login is created.
#
# Parameters:
# full_name        - Teacher full name
# department       - Teacher department
# email            - Teacher email address
# phone            - Teacher phone number
# username         - Teacher chosen username
# password         - Teacher chosen password
# confirm_password - Password confirmation
#
# Returns:
# True/False and a message
# ==========================================================
def register_teacher(
    full_name,
    department,
    email,
    phone,
    username,
    password,
    confirm_password
):

    # Check required fields
    if not full_name.strip() or not username.strip() or not password.strip():
        return False, "Name, username and password are required."

    # Check whether password and confirm password match
    if password != confirm_password:
        return False, "Passwords do not match."

    # Connect to MySQL database
    conn = get_connection()
    cur = conn.cursor()

    try:
        # --------------------------------------------------
        # Check duplicate username or email
        # --------------------------------------------------
        # This prevents two teachers from using the same
        # username or email address.
        cur.execute(
            "SELECT teacher_id FROM teachers WHERE username=%s OR email=%s",
            (username.strip(), email.strip())
        )

        if cur.fetchone():
            return False, "Username or email already exists."

        # Hash the teacher's chosen password before saving it.
        # The plain-text password is never stored in MySQL.
        hashed_password = hash_password(password)

        # --------------------------------------------------
        # Insert teacher registration request
        # --------------------------------------------------
        # Status is set to Pending because admin approval
        # is required before the teacher can log in.
        cur.execute("""
            INSERT INTO teachers
            (
                full_name,
                department,
                email,
                phone,
                username,
                password,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """, (
            full_name.strip(),
            department.strip(),
            email.strip(),
            phone.strip(),
            username.strip(),
            hashed_password
        ))

        # Save changes into database
        conn.commit()

        return True, "Teacher registration submitted. Please wait for admin approval."

    except Exception as e:
        # Undo changes if an error occurs
        conn.rollback()

        return False, f"Teacher registration failed: {e}"

    finally:
        # Always close database connection
        conn.close()


# ==========================================================
# Function: get_pending_teachers()
#
# Purpose:
# Load teacher registration records from the database.
#
# Used By:
# Admin dashboard page "Teacher Approval".
#
# Returns:
# Pandas DataFrame containing teacher details.
# ==========================================================
def get_pending_teachers():

    # Import pandas only inside the function because it is
    # used only for creating table/dataframe output.
    import pandas as pd

    # Connect to MySQL database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # ------------------------------------------------------
    # Load teacher requests
    # ------------------------------------------------------
    # The latest teacher registration appears first.
    cur.execute("""
        SELECT
            teacher_id,
            full_name,
            department,
            email,
            phone,
            username,
            status
        FROM teachers
        ORDER BY teacher_id DESC
    """)

    # Convert query result into pandas DataFrame
    df = pd.DataFrame(cur.fetchall())

    # Close database connection
    conn.close()

    return df


# ==========================================================
# Function: approve_teacher()
#
# Purpose:
# Approve a teacher registration request.
#
# Process:
# 1. Find teacher record by teacher_id.
# 2. Change teacher status to Approved.
# 3. Check whether teacher login already exists.
# 4. If login does not exist, create it in users table.
# 5. Send approval email to teacher.
#
# Parameters:
# teacher_id - ID of the teacher selected by admin
#
# Returns:
# True/False and status message
# ==========================================================
def approve_teacher(teacher_id):

    # Connect to MySQL database
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # --------------------------------------------------
        # Get selected teacher details
        # --------------------------------------------------
        cur.execute(
            "SELECT * FROM teachers WHERE teacher_id=%s",
            (int(teacher_id),)
        )

        teacher = cur.fetchone()

        # If no teacher exists with this ID
        if not teacher:
            return False, "Teacher not found."

        # --------------------------------------------------
        # Update teacher status to Approved
        # --------------------------------------------------
        cur.execute("""
            UPDATE teachers
            SET status='Approved'
            WHERE teacher_id=%s
        """, (int(teacher_id),))

        # --------------------------------------------------
        # Check if teacher login already exists
        # --------------------------------------------------
        cur.execute(
            "SELECT user_id FROM users WHERE username=%s",
            (teacher["username"],)
        )

        exists = cur.fetchone()

        # --------------------------------------------------
        # Create teacher login account if it does not exist
        # --------------------------------------------------
        # Teacher role is inserted into users table.
        # student_id is NULL because this is a teacher account.
        if not exists:
            cur.execute("""
                INSERT INTO users
                (
                    username,
                    password,
                    role,
                    student_id
                )
                VALUES (%s, %s, 'Teacher', NULL)
            """, (
                teacher["username"],
                teacher["password"]
            ))

        # Save database changes first
        conn.commit()

    except Exception as e:
        # Undo database changes if approval fails
        conn.rollback()

        return False, f"Teacher approval failed: {e}"

    finally:
        # Close database connection before sending email
        conn.close()

    # ------------------------------------------------------
    # Send approval email after successful database update
    # ------------------------------------------------------
    # Email is sent after commit so even if email fails,
    # teacher approval is still saved in the database.
    try:
        send_teacher_approval_email(
            teacher["email"],
            teacher["full_name"],
            teacher["username"]
        )

        return True, "Teacher approved successfully and approval email sent."

    except Exception as e:
        return True, f"Teacher approved successfully, but email failed: {e}"


# ==========================================================
# Function: reject_teacher()
#
# Purpose:
# Reject a teacher registration request.
#
# Process:
# 1. Find teacher request using teacher_id.
# 2. Change status to Rejected.
# 3. Save update into database.
#
# Note:
# Rejected teachers are not added to the users table,
# so they cannot log in.
#
# Parameters:
# teacher_id - ID of the teacher selected by admin
#
# Returns:
# True/False and message
# ==========================================================
def reject_teacher(teacher_id):

    # Connect to MySQL database
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Update teacher status to Rejected
        cur.execute("""
            UPDATE teachers
            SET status='Rejected'
            WHERE teacher_id=%s
        """, (int(teacher_id),))

        # Save database changes
        conn.commit()

        return True, "Teacher rejected."

    except Exception as e:
        # Undo changes if rejection fails
        conn.rollback()

        return False, f"Teacher rejection failed: {e}"

    finally:
        # Close database connection
        conn.close()
