# -------------------------------------------------------------
# LOGIN SYSTEM FOR ADMIN / TEACHER
# -------------------------------------------------------------

import mysql.connector

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
        print("\n❌ Database connection failed.")
        print("Reason:", err)
        return None


def login():
    print("\n==============================================")
    print("                LOGIN SYSTEM")
    print("==============================================")

    username = input("Enter Username: ")
    password = input("Enter Password: ")

    connection = get_connection()

    if connection:
        cursor = connection.cursor()

        query = "SELECT role FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            role = result[0]
            print(f"\n✔ Login Successful! Logged in as: {role}")
            return role
        else:
            print("\n❌ Invalid username or password.")
            return None

    else:
        return None
