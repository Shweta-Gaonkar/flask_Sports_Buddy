from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'sports_buddy_secret'

DB_NAME = "sports_buddy.db"

# ✅ Auto-initialize DB
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                city TEXT NOT NULL,
                area TEXT NOT NULL,
                skill_level TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        conn.commit()

# ✅ Run once on startup
init_db()

# 🔁 Helper to run SQL
def run_query(query, params=(), one=False):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.commit()
        return result[0] if one and result else result

# 🏠 Home route
@app.route('/')
def home():
    return redirect('/login')

# 👤 Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        run_query("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (
            request.form['name'],
            request.form['email'],
            request.form['password']
        ))
        return redirect('/login')
    return render_template('register.html')

# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = run_query("SELECT * FROM users WHERE email=? AND password=?", (
            request.form['email'],
            request.form['password']
        ), one=True)
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# 📋 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    events = run_query("SELECT * FROM events WHERE created_by=?", (session['user_id'],))
    return render_template('dashboard.html', events=events)

# ➕ Add Event
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        run_query("""
            INSERT INTO events (sport, city, area, skill_level, date, time, location, description, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['sport'],
            request.form['city'],
            request.form['area'],
            request.form['skill_level'],
            request.form['date'],
            request.form['time'],
            request.form['location'],
            request.form['description'],
            session['user_id']
        ))
        return redirect('/dashboard')
    return render_template('add_event.html')

# ✏️ Edit Event
@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if 'user_id' not in session:
        return redirect('/login')
    event = run_query("SELECT * FROM events WHERE id = ? AND created_by = ?", (event_id, session['user_id']), one=True)
    if not event:
        return "Event not found or unauthorized"
    if request.method == 'POST':
        run_query("""
            UPDATE events SET sport=?, city=?, area=?, skill_level=?, date=?, time=?, location=?, description=?
            WHERE id=? AND created_by=?
        """, (
            request.form['sport'],
            request.form['city'],
            request.form['area'],
            request.form['skill_level'],
            request.form['date'],
            request.form['time'],
            request.form['location'],
            request.form['description'],
            event_id,
            session['user_id']
        ))
        return redirect('/dashboard')
    return render_template('edit_event.html', event=event)

# 🗑️ Delete Event
@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    if 'user_id' not in session:
        return redirect('/login')
    run_query("DELETE FROM events WHERE id=? AND created_by=?", (event_id, session['user_id']))
    return redirect('/dashboard')

# 🌍 Explore Events
@app.route('/explore')
def explore():
    if 'user_id' not in session:
        return redirect('/login')
    events = run_query("SELECT events.*, users.name FROM events JOIN users ON events.created_by = users.id WHERE events.created_by != ?", (session['user_id'],))
    return render_template('explore.html', events=events)

# 🔜 Join route (for later)
@app.route('/join/<int:event_id>')
def join(event_id):
    return "Join functionality coming soon!"

if __name__ == '__main__':
    app.run(debug=True)
