from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = "mysecretkey123"
TICKET_PRICE = 100

# Initialize database if not exists
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        destination TEXT,
        date TEXT,
        user_email TEXT,
        user_phone TEXT,
        ticket_code TEXT,
        price REAL
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- HELPERS --------------------
def generate_ticket_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return "Bus Ticket System Running"

@app.route('/register', methods=['GET','POST'])
def register():
    message = ""
    if request.method=='POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?",(email,))
        user = cursor.fetchone()
        
        if user:
            message = "Email already registered!"
        else:
            cursor.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                           (name,email,hashed_password))
            conn.commit()
            message = "Registered successfully! You can login now."
        conn.close()
    return render_template('register.html', message=message)

@app.route('/login', methods=['GET','POST'])
def login():
    message = ""
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?",(email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user'] = email
            return redirect('/dashboard')
        else:
            message = "Invalid Email or Password"
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    user_email = session['user']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_email=?",(user_email,))
    total_bookings = cursor.fetchone()[0]
    conn.close()
    
    return render_template('dashboard.html', user=user_email, total_bookings=total_bookings)

@app.route('/booking', methods=['GET','POST'])
def booking():
    if 'user' not in session:
        return redirect('/login')
    
    message = ""
    if request.method=='POST':
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']
        user_phone = request.form['user_phone']
        user_email = session['user']
        
        if not user_phone.isdigit() or len(user_phone)<10:
            message = "Enter a valid 10-digit phone number"
            return render_template('booking.html', message=message)
        
        ticket_code = generate_ticket_code()
        price = TICKET_PRICE
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bookings (source,destination,date,user_email,user_phone,ticket_code,price)
            VALUES (?,?,?,?,?,?,?)
        """, (source,destination,date,user_email,user_phone,ticket_code,price))
        conn.commit()
        conn.close()
        
        message = f"Ticket booked successfully! Code: {ticket_code} | Price: ₹{price}"
    
    return render_template('booking.html', message=message)
# -------------------- VIEW BOOKINGS --------------------
@app.route('/view_bookings')
def view_bookings():
    if 'user' not in session:
        return redirect('/login')
    
    user_email = session['user']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_email=? ORDER BY date", (user_email,))
    bookings = cursor.fetchall()
    conn.close()
    
    return render_template('view_bookings.html', bookings=bookings)

# -------------------- DELETE BOOKING --------------------
@app.route('/delete_booking/<int:id>')
def delete_booking(id):
    if 'user' not in session:
        return redirect('/login')
    
    user_email = session['user']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id=? AND user_email=?", (id, user_email))
    conn.commit()
    conn.close()
    
    return redirect('/view_bookings')

# -------------------- EDIT BOOKING --------------------
@app.route('/edit_booking/<int:id>', methods=['GET','POST'])
def edit_booking(id):
    if 'user' not in session:
        return redirect('/login')
    
    user_email = session['user']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=? AND user_email=?", (id, user_email))
    booking = cursor.fetchone()
    
    if not booking:
        conn.close()
        return "Booking not found or access denied"
    
    if request.method=='POST':
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']
        user_phone = request.form['user_phone']
        
        cursor.execute("""
            UPDATE bookings 
            SET source=?, destination=?, date=?, user_phone=?
            WHERE id=? AND user_email=?
        """, (source, destination, date, user_phone, id, user_email))
        conn.commit()
        conn.close()
        return redirect('/view_bookings')
    
    conn.close()
    return render_template('edit_booking.html', booking=booking)
if __name__=='__main__':
    app.run(debug=True)