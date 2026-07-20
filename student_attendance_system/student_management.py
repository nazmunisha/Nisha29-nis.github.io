# ==========================================================
#
#
# Purpose:
# This module manages all student-related operations.
#
# Features:
# • Validate student email
# • Generate unique username
# • Convert uploaded image into bytes
# • Create student login account
# • Add new student
# • Update student information
# • Delete student and related records
#
# Technologies Used:
# • Python
# • Regular Expressions (re)
# • MySQL
# • Gmail SMTP
# ==========================================================

# Import Regular Expression library
# Used for email validation and username generation
import re

# Import email function
# Sends login credentials to newly registered students
from email_utils import send_student_login_email

# Import database connection
from database import get_connection
from password_utils import hash_password


# ==========================================================
# Function: valid_email()
#
# Purpose:
# Validate whether the email address entered by the user
# follows the correct email format.
#
# Example:
# student@gmail.com ✓
# student123@abc.co.nz ✓
# student@gmail ✗
#
# Returns:
# True  -> Valid Email
# False -> Invalid Email
# ==========================================================
def valid_email(email):

    # Regular Expression pattern for email validation
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    # Return True if email matches pattern
    return re.match(pattern, email) is not None


# ==========================================================
# Function: make_username()
#
# Purpose:
# Automatically generate a username from the student's name.
#
# Example:
# John Smith
# ↓
# johnsmith
#
# If the generated username already exists,
# another function adds numbers to make it unique.
#
# Returns:
# Username string
# ==========================================================
def make_username(name):

    # Remove spaces and special characters
    username = re.sub(r"[^a-z0-9]", "", str(name).lower())

    # If empty, use default username
    return username if username else "student"


# ==========================================================
# Function: image_bytes()
#
# Purpose:
# Convert uploaded image into binary format (bytes)
# before storing it in the MySQL database.
#
# Returns:
# Image bytes or None
# ==========================================================
def image_bytes(uploaded_file):

    if uploaded_file:
        return uploaded_file.getvalue()

    return None


# ==========================================================
# Function: create_student_login()
#
# Purpose:
# Automatically create a login account for every
# newly registered student.
#
# Process:
# 1. Generate username.
# 2. Check username uniqueness.
# 3. Generate password.
# 4. Insert login details into Users table.
#
# Returns:
# Username and Password
# ==========================================================
def create_student_login(cur, student_id, name):

    # Generate base username
    base = make_username(name)

    username = base

    count = 1

    # Check whether username already exists
    while True:

        cur.execute(
            "SELECT user_id FROM users WHERE username=%s",
            (username,)
        )

        if not cur.fetchone():
            break

        # If username exists,
        # append number to create unique username
        count += 1
        username = f"{base}{count}"

    # Create the student's temporary plain-text password.
    # This value is returned only so it can be shown/sent to
    # the student. It is never stored directly in MySQL.
    password = f"{username}{student_id}"

    # Convert the temporary password into a secure bcrypt hash.
    hashed_password = hash_password(password)

    # Store only the bcrypt hash in the users table.
    cur.execute("""
        INSERT INTO users
        (username, password, role, student_id)
        VALUES (%s, %s, 'Student', %s)
    """, (
        username,
        hashed_password,
        int(student_id)
    ))

    # Return the original temporary password for the email/UI.
    return username, password


# ==========================================================
# Function: add_student()
#
# Purpose:
# Add a new student into the Attendance Management System.
#
# Process:
# 1. Validate input.
# 2. Check duplicate Roll Number.
# 3. Store student details.
# 4. Store profile photo.
# 5. Create login account.
# 6. Send login details through email.
#
# Returns:
# Success status, message, username and password.
# ==========================================================
def add_student(
    roll_no,
    name,
    department,
    class_name,
    email,
    phone,
    photo_file
):

    # Connect to database
    conn = get_connection()

    cur = conn.cursor()

    try:

        # Validate Roll Number
        if not roll_no.strip():
            return False, "Roll Number is required.", None, None

        # Validate Student Name
        if not name.strip():
            return False, "Student Name is required.", None, None

        # Validate Email Format
        if email.strip() and not valid_email(email.strip()):
            return False, "Invalid email address.", None, None

        # Check duplicate Roll Number
        cur.execute(
            "SELECT student_id FROM students WHERE roll_no=%s",
            (roll_no.strip(),)
        )

        if cur.fetchone():
            return False, "Roll Number already exists.", None, None

        # Insert student record into Students table
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
            (%s,%s,%s,%s,%s,%s,%s)
        """, (
            roll_no.strip(),
            name.strip(),
            department.strip(),
            class_name.strip(),
            email.strip(),
            phone.strip(),
            image_bytes(photo_file)
        ))

        # Get automatically generated Student ID
        student_id = cur.lastrowid

        # Create Student Login Account
        username, password = create_student_login(
            cur,
            student_id,
            name.strip()
        )

        # Save changes
        conn.commit()

    except Exception as e:

        # Undo changes if an error occurs
        conn.rollback()

        return False, f"Student could not be added: {e}", None, None

    finally:

        # Close database connection
        conn.close()

    # ------------------------------------------------------
    # Send Login Details to Student Email
    # ------------------------------------------------------

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

            message = (
                f"Student added successfully. "
                f"Login details emailed to {email.strip()}."
            )

        except Exception as e:

            print("Email sending failed:", e)

            message = (
                f"Student added successfully, "
                f"but email failed: {e}"
            )

    else:

        message = (
            "Student added successfully. "
            "No email was provided."
        )

    return True, message, username, password


# ==========================================================
# Function: update_student()
#
# Purpose:
# Update an existing student's information.
#
# Process:
# • Update personal details.
# • Update profile photo if a new photo is uploaded.
#
# Returns:
# None
# ==========================================================
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

    # Connect to database
    conn = get_connection()

    cur = conn.cursor()

    try:

        # Update with new profile photo
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

        # Update without changing profile photo
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

        # Save changes
        conn.commit()

    except Exception:

        # Undo changes if update fails
        conn.rollback()

        raise

    finally:

        # Close database connection
        conn.close()


# ==========================================================
# Function: delete_student()
#
# Purpose:
# Delete a student and all related records from
# the Attendance Management System.
#
# Process:
# 1. Delete attendance history.
# 2. Delete registered face.
# 3. Delete login account.
# 4. Delete student record.
#
# Returns:
# None
# ==========================================================
def delete_student(student_id):

    # Connect to database
    conn = get_connection()

    cur = conn.cursor()

    try:

        # Delete attendance records
        cur.execute(
            "DELETE FROM attendance WHERE student_id=%s",
            (int(student_id),)
        )

        # Delete registered face
        cur.execute(
            "DELETE FROM face_data WHERE student_id=%s",
            (int(student_id),)
        )

        # Delete login account
        cur.execute(
            "DELETE FROM users WHERE student_id=%s",
            (int(student_id),)
        )

        # Delete student record
        cur.execute(
            "DELETE FROM students WHERE student_id=%s",
            (int(student_id),)
        )

        # Save changes
        conn.commit()

    except Exception:

        # Undo deletion if any error occurs
        conn.rollback()

        raise

    finally:

        # Close database connection
        conn.close()