# Import MySQL connector library
# This allows Python to connect with MySQL database
import mysql.connector

# Password helpers used for secure account creation and migration
from password_utils import hash_password, is_bcrypt_hash


# Database configuration
# These details are used to connect Python with MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Nisha@1985",
    "database": "attendance_system",
}


# ==========================================================
# Function: get_connection()
# Purpose : Create and return a connection to MySQL database
# ==========================================================
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ==========================================================
# Function: ensure_schema()
# Purpose : Create required database tables if they do not exist
# ==========================================================
def ensure_schema():

    # Connect to database
    conn = get_connection()

    # Create cursor to execute SQL queries
    cur = conn.cursor()

    # ------------------------------------------------------
    # Create students table
    # Stores student personal details and profile photo
    # ------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INT AUTO_INCREMENT PRIMARY KEY,
            roll_no VARCHAR(100) UNIQUE,
            name VARCHAR(255) NOT NULL,
            department VARCHAR(255),
            class VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(100),
            photo LONGBLOB NULL
        )
    """)

    # ------------------------------------------------------
    # Create users table
    # Stores login details for Admin, Teacher, and Student
    # ------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('Admin','Teacher','Student') NOT NULL,
            student_id INT NULL
        )
    """)

    # ------------------------------------------------------
    # Create attendance table
    # Stores attendance date, time, status, and source
    # ------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status VARCHAR(50) DEFAULT 'Present',
            source VARCHAR(100) DEFAULT 'FaceRecognition',
            device_type ENUM(
                'Laptop',
                'Mobile',
                'TeacherDashboard',
                'FaceRecognition',
                'Manual'
            ) DEFAULT 'Laptop'
        )
    """)

    # ------------------------------------------------------
    # Create face_data table
    # Stores processed face image/encoding for each student
    # One student can have one registered face record
    # ------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS face_data (
            face_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL UNIQUE,
            encoding LONGBLOB NOT NULL
        )
    """)

    # ------------------------------------------------------
    # Create teachers table
    # Stores teacher registration details and approval status
    # ------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20),
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending'
        )
    """)

    # ------------------------------------------------------
    # Add photo column if old students table does not have it
    # This prevents errors if the table already existed earlier
    # ------------------------------------------------------
    try:
        cur.execute("ALTER TABLE students ADD COLUMN photo LONGBLOB NULL")
    except mysql.connector.Error:
        pass

    # ------------------------------------------------------
    # Create default admin account if users table is empty
    # This allows the system owner to login first time
    # ------------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM users")

    if cur.fetchone()[0] == 0:
        # Store the default admin password as a bcrypt hash.
        default_admin_hash = hash_password("admin123")

        cur.execute("""
            INSERT INTO users (username, password, role, student_id)
            VALUES (%s, %s, 'Admin', NULL)
        """, (
            "admin",
            default_admin_hash
        ))

    # ------------------------------------------------------
    # Migrate older plain-text passwords to bcrypt.
    #
    # This keeps existing usernames/passwords working while
    # ensuring their database values become secure hashes.
    # ------------------------------------------------------
    cur.execute("SELECT user_id, password FROM users")

    for user_id, stored_password in cur.fetchall():
        if not is_bcrypt_hash(stored_password):
            cur.execute(
                "UPDATE users SET password=%s WHERE user_id=%s",
                (hash_password(stored_password), user_id)
            )

    # The teachers table also stores the password while a
    # registration request is pending. Protect those values too.
    cur.execute("SELECT teacher_id, password FROM teachers")

    for teacher_id, stored_password in cur.fetchall():
        if not is_bcrypt_hash(stored_password):
            cur.execute(
                "UPDATE teachers SET password=%s WHERE teacher_id=%s",
                (hash_password(stored_password), teacher_id)
            )

    # Save all database changes
    conn.commit()

    # Close database connection
    conn.close()


# ==========================================================
# Function: fetch_dataframe()
# Purpose : Run any SQL query and return result as pandas table
# ==========================================================
def fetch_dataframe(query, params=None):

    # Import pandas for table/dataframe format
    import pandas as pd

    # Connect to database
    conn = get_connection()

    # Cursor returns rows as dictionary
    cur = conn.cursor(dictionary=True)

    # Execute SQL query
    cur.execute(query, params or ())

    # Convert result into pandas DataFrame
    df = pd.DataFrame(cur.fetchall())

    # Close database connection
    conn.close()

    # Return table data
    return df


# ==========================================================
# Function: load_data()
#
# Purpose:
# Load all data required by the Attendance Management System
# dashboard.
#
# This function retrieves:
# 1. Student information
# 2. Attendance records with student details
# 3. Registered face IDs
#
# Returns:
# students_df           -> Student information
# attendance_df         -> Attendance records
# registered_face_ids   -> Set of students with registered faces
# ==========================================================
def load_data():

    # Import pandas to store SQL query results as DataFrames
    import pandas as pd

    # Connect to MySQL database
    conn = get_connection()

    # Dictionary cursor returns column names with values
    cur = conn.cursor(dictionary=True)

    # ======================================================
    # STEP 1: Load Student Information
    # ======================================================
    # Retrieve all students from the students table.
    # These details are displayed in the Student Management
    # page and used throughout the dashboard.
    # ======================================================
    cur.execute("""
        SELECT
            student_id,
            roll_no,
            name,
            department,
            class,
            email,
            phone,
            photo
        FROM students
        ORDER BY student_id DESC
    """)

    # Convert SQL result into a pandas DataFrame
    students_df = pd.DataFrame(cur.fetchall())

    # ======================================================
    # STEP 2: Load Attendance Records
    # ======================================================
    # Join attendance and student tables so that the dashboard
    # can display student names instead of only student IDs.
    #
    # TIME_FORMAT() converts MySQL TIME into a readable format
    # such as 09:35:20 AM.
    # ======================================================
    cur.execute("""
        SELECT
            a.attendance_id,
            a.student_id,

            -- Student Information
            s.name AS student_name,
            s.roll_no,
            s.department,
            s.class,

            -- Attendance Details
            a.date,

            -- Display time in AM/PM format
            TIME_FORMAT(a.time, '%h:%i:%s %p') AS time,

            a.status,
            a.source,
            a.device_type

        FROM attendance a

        -- Join with students table using student_id
        LEFT JOIN students s
            ON a.student_id = s.student_id

        -- Show latest attendance first
        ORDER BY a.date DESC, a.time DESC
    """)

    # Store attendance records inside a DataFrame
    attendance_df = pd.DataFrame(cur.fetchall())

    # ======================================================
    # STEP 3: Load Registered Face IDs
    # ======================================================
    # Read all student IDs that have a registered face.
    # This helps the dashboard determine whether a student's
    # face has already been registered.
    # ======================================================
    cur.execute("""
        SELECT student_id
        FROM face_data
    """)

    # Convert student IDs into a Python set
    registered_face_ids = {
        int(row["student_id"])
        for row in cur.fetchall()
    }

    # ======================================================
    # STEP 4: Close Database Connection
    # ======================================================
    conn.close()

    # ======================================================
    # Return all loaded data
    # ======================================================
    return (
        students_df,
        attendance_df,
        registered_face_ids
    )