# IMPORT: Setup + Menus + Authentication
from database import setup_database
from helper import register, login
from menus import admin_menu, customer_menu

# INITIALIZE DATABASE
setup_database()

# MAIN PROGRAM LOOP
print("=== Car Rental System ===")

while True:
    print("\n1. Register")
    print("2. Login")
    print("3. Exit")

    choice = input("Choose: ")

    if choice == "1":
        register()
    elif choice == "2":
        user = login()
        if user:
              # user[3] = role column
            if user[3] == "admin":
                admin_menu()
            else:
                customer_menu(user)
    elif choice == "3":
        print("Goodbye.")
        break
