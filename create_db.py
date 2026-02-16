import sqlite3

# Connect (or create) the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# -------------------- USERS TABLE --------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT)""")

# -------------------- BOOKINGS TABLE --------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    destination TEXT,
    date TEXT,
    user_email TEXT,
    user_phone TEXT,
    ticket_code TEXT,
    price REAL)""")

conn.commit()
conn.close()
print("Database and tables created successfully!")