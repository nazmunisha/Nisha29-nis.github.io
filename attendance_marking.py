# -------------------------------------------------------------
# ATTENDANCE MARKING (Protected by Login)
# Only Admin / Teacher can access this module
# -------------------------------------------------------------

from login import login
import mysql.connector
from datetime import datetime

# -------------------------------------------------------------
# Database Connection
# -------------------------------------------------------------
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Nisha@1985",
            database="attendance_system"
        )
        return connection
    except mysql.connector.Error as err:
        print("\n❌ ERROR: Could not connect to the database.")
        print("Reason:", err)
        return None


# -------------------------------------------------------------
# FUNCTION: mark_attendance()
# Called from app.py
# -------------------------------------------------------------
def mark_attendance():

    # Step 1: Login first
    role = login()

    if role not in ["Admin", "Teacher"]:
        print("\n❌ Access Denied. Only Admin/Teacher can mark attendance.")
        return

    print("\n✔ Access Granted. You can now mark attendance.\n")

    print("==============================================")
    print("        ATTENDANCE MARKING SYSTEM")
    print("==============================================")

    student_id = input("Enter Student ID: ")

    connection = get_connection()

    if connection:
        cursor = connection.cursor()

        # Step 2: Check if student exists
        check_query = "SELECT name FROM students WHERE student_id = %s"
        cursor.execute(check_query, (student_id,))
        result = cursor.fetchone()

        if result:
            student_name = result[0]
            print(f"\n✔ Student Found: {student_name}")

            # Step 3: Mark attendance
            now = datetime.now()
            date = now.date()
            time = now.strftime("%H:%M:%S")

            insert_query = """
                INSERT INTO attendance (student_id, date, time, status, source, device_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            try:
                cursor.execute(insert_query, (
                    student_id,
                    date,
                    time,
                    "Present",
                    "Manual",
                    "Laptop"
                ))
                connection.commit()

                print("\n✔ SUCCESS: Attendance marked successfully!")
                print("----------------------------------------------")
                print(f"Student Name,ID: {student_name} ({student_id})")
                print(f"Status : Present")
                print(f"Date   : {date}")
                print(f"Time   : {time}")
                print("----------------------------------------------\n")

            except mysql.connector.Error as err:
                print("\n❌ ERROR: Could not save attendance.")
                print("Reason:", err)

        else:
            print("\n❌ ERROR: No student found with that Student ID.")

        cursor.close()
        connection.close()

    else:
        print("\n❌ Program stopped because database connection failed.\n")
