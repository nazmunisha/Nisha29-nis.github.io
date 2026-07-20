# IMPORT: Database Connection
from database import get_connection

# FUNCTION: register()
def register():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- Register ---")
    username = input("Username: ")
    password = input("Password: ")

    print("Select role:")
    print("1. Customer")
    print("2. Admin")
    role_choice = input("Choose: ")

    if role_choice == "1":
        role = "customer"
    elif role_choice == "2":
        role = "admin"
    else:
        print("Invalid choice. Defaulting to customer.")
        role = "customer"

    try:
        cur.execute("INSERT INTO users(username, password, role) VALUES (?, ?, ?)",
                    (username, password, role))
        conn.commit()
        print(f"{role.capitalize()} registered successfully.")
    except:
        print("Username already exists.")


# FUNCTION: login()
def login():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- Login ---")
    username = input("Username: ")
    password = input("Password: ")

    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()

    return user
