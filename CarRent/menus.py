#   IMPORT FUNCTIONS
from admin_function import add_car, view_cars_admin, delete_car, approve_rentals
from customer_functions import view_available_cars, book_car


# FUNCTION: admin_menu()
def admin_menu():
    while True:
        print("\n--- Admin Menu ---")
        print("1. Add Car")      
        print("2. View Cars")
        print("3. Delete Car")
        print("4. Approve/Reject Rentals")
        print("5. Logout")

        choice = input("Choose: ")

        if choice == "1":
            add_car()         # Calls function to add a new car
        elif choice == "2":
            view_cars_admin() # Calls function to view all cars
        elif choice == "3":
            delete_car()        # Calls function to delete a car
        elif choice == "4":
        
            approve_rentals()    # Calls function to approve/reject rentals
        elif choice == "5":      # Exit admin menu
            break


#   FUNCTION: customer_menu()

def customer_menu(user):
    while True:
        print("\n--- Customer Menu ---")
        print("1. View Available Cars")
        print("2. Book a Car")
        print("3. Logout")

        choice = input("Choose: ")

        if choice == "1":
            view_available_cars()  # Shows cars available for booking
        elif choice == "2":
            book_car(user)           # Books a car for the logged-in user
        elif choice == "3":
            break                  # Exit customer menu
