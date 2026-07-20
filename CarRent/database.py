import sqlite3


#   DATABASE SINGLETON CLASS


class Database:
    _instance = None   # Holds the single instance of this class

    def __new__(cls):  # __new__ controls object creation BEFORE __init__
       
        if cls._instance is None:
            
            cls._instance = super(Database, cls).__new__(cls) # Create the instance only once
           
            cls._instance.conn = sqlite3.connect("data.db")  # Create the database connection only once
        return cls._instance

    def get_connection(self):
        
        return self.conn # Returns the same connection every time



#   FUNCTION: get_connection()

def get_connection():
    return Database().get_connection()


#   FUNCTION: setup_database()

def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    
    # USERS TABLE
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    
    # CARS TABLE
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        make TEXT,
        model TEXT,
        year INTEGER,
        mileage INTEGER,
        available_now INTEGER,
        min_days INTEGER,
        max_days INTEGER,
        daily_rate REAL
    )
    """)


    # RENTALS TABLE

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rentals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        car_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        total_days INTEGER,
        total_fee REAL,
        status TEXT
    )
    """)

    conn.commit()
    
