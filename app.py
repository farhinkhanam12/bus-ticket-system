from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = "mysecretkey123"

DATABASE = "database.db"
TICKET_PRICE = 100


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
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


# ---------------- HELPERS ----------------
def generate_ticket_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )
            conn.commit()
            message = "Registered Successfully!"
        except:
            message = "Email already exists!"

        conn.close()

    return render_template("register.html", message=message)


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user"] = email
            return redirect("/dashboard")
        else:
            message = "Invalid credentials"

    return render_template("login.html", message=message)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_email=?", (user_email,))
    total = cursor.fetchone()[0]
    conn.close()

    return render_template("dashboard.html",
                           user=user_email,
                           total_bookings=total)


# ---------------- BOOKING ----------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user" not in session:
        return redirect("/login")

    message = ""

    if request.method == "POST":
        source = request.form["source"]
        destination = request.form["destination"]
        date = request.form["date"]
        phone = request.form["user_phone"]

        ticket_code = generate_ticket_code()
        price = TICKET_PRICE

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO bookings
        (source,destination,date,user_email,user_phone,ticket_code,price)
        VALUES(?,?,?,?,?,?,?)
        """, (source, destination, date,
              session["user"], phone,
              ticket_code, price))

        conn.commit()
        conn.close()

        message = f"Ticket Booked! Code: {ticket_code} | Price ₹{price}"

    return render_template("booking.html", message=message)


# ---------------- VIEW BOOKINGS ----------------
@app.route("/view_bookings")
def view_bookings():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM bookings WHERE user_email=?",
        (session["user"],)
    )
    bookings = cursor.fetchall()
    conn.close()

    return render_template("view_bookings.html", bookings=bookings)


# ---------------- DELETE ----------------
@app.route("/delete_booking/<int:id>")
def delete_booking(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM bookings WHERE id=? AND user_email=?",
        (id, session["user"])
    )
    conn.commit()
    conn.close()

    return redirect("/view_bookings")


# ---------------- EDIT ----------------
@app.route("/edit_booking/<int:id>", methods=["GET", "POST"])
def edit_booking(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM bookings WHERE id=? AND user_email=?",
        (id, session["user"])
    )
    booking = cursor.fetchone()

    if request.method == "POST":
        source = request.form["source"]
        destination = request.form["destination"]
        date = request.form["date"]
        phone = request.form["user_phone"]

        cursor.execute("""
        UPDATE bookings
        SET source=?, destination=?, date=?, user_phone=?
        WHERE id=? AND user_email=?
        """, (source, destination, date, phone,
              id, session["user"]))

        conn.commit()
        conn.close()
        return redirect("/view_bookings")

    conn.close()
    return render_template("edit_booking.html", booking=booking)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)