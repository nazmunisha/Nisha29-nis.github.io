
# IMPORT: Database Connection
from database import get_connection

# FUNCTION: add_car()
def add_car():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- Add Car ---")
    make = input("Make: ")
    model = input("Model: ")
    year = int(input("Year: "))
    mileage = int(input("Mileage: "))
    min_days = int(input("Minimum rental days: "))
    max_days = int(input("Maximum rental days: "))
    daily_rate = float(input("Daily rate: "))

    cur.execute("""
        INSERT INTO cars(make, model, year, mileage, available_now, min_days, max_days, daily_rate)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?)
    """, (make, model, year, mileage, min_days, max_days, daily_rate))

    conn.commit()
    print("Car added successfully.")

# FUNCTION: view_cars_admin()
def view_cars_admin():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- All Cars ---")
    cur.execute("SELECT * FROM cars")
    for car in cur.fetchall():
        print(car)

# FUNCTION: delete_car()

def delete_car():
    conn = get_connection()
    cur = conn.cursor()

    car_id = int(input("Enter car ID to delete: "))
    cur.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()

    print("Car deleted.")


# FUNCTION: approve_rentals()

def approve_rentals():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- Pending Rentals ---")
    cur.execute("SELECT * FROM rentals WHERE status='pending'")
    rentals = cur.fetchall()

    for r in rentals:
        print(r)

    rid = int(input("Enter rental ID to approve/reject: "))
    choice = input("Approve (a) or Reject (r): ")

    if choice == "a":
        cur.execute("UPDATE rentals SET status='approved' WHERE id=?", (rid,))
    else:
        cur.execute("UPDATE rentals SET status='rejected' WHERE id=?", (rid,))

    conn.commit()
    print("Done.")
