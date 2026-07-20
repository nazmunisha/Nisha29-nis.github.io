
# IMPORT: Database Connection
from database import get_connection
from datetime import datetime

# FUNCTION: view_available_cars()
def view_available_cars():
    conn = get_connection()
    cur = conn.cursor()

    print("\n--- Available Cars ---")
    cur.execute("SELECT * FROM cars WHERE available_now=1")
    for car in cur.fetchall():
        print(car)

    
# FUNCTION: book_car()
def book_car(user):
    conn = get_connection()
    cur = conn.cursor()

  # Show available cars before booking
    view_available_cars()
    car_id = int(input("Enter car ID to book: "))

    start = input("Start date (YYYY-MM-DD): ")
    end = input("End date (YYYY-MM-DD): ")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    total_days = (end_date - start_date).days

 # Fetch car rental rules
    cur.execute("SELECT daily_rate, min_days, max_days FROM cars WHERE id=?", (car_id,))
    car = cur.fetchone()

    if not car:
        print("Car not found.")
        return

    rate, min_days, max_days = car


    # Validate rental duration
    if total_days < min_days or total_days > max_days:
        print("Rental days not allowed.")
        return

    total_fee = total_days * rate
 # Insert rental request
    cur.execute("""
        INSERT INTO rentals(customer_id, car_id, start_date, end_date, total_days, total_fee, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (user[0], car_id, start, end, total_days, total_fee))

    conn.commit()
    print("Booking submitted.")
