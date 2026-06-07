#!/usr/bin/env python3
"""
MoneyMom - REAL BIF 10,000 Note Platform
Uses actual scanned note images
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
import io
import sqlite3
import datetime
import os
import secrets
import base64
from PIL import Image
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Load your real note images
with open('bif_front.jpg', 'rb') as f:
    FRONT_IMG_BASE64 = base64.b64encode(f.read()).decode()
with open('bif_back.jpg', 'rb') as f:
    BACK_IMG_BASE64 = base64.b64encode(f.read()).decode()

def init_db():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY, user_id INTEGER, serial_number TEXT, front_img TEXT, back_img TEXT, created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, ip TEXT, created TEXT)''')
    
    admin_pass = generate_password_hash("08800Mpc+_+")
    c.execute("SELECT * FROM users WHERE username=?", ("Mpc",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ("Mpc", admin_pass, "0.0.0.0", datetime.datetime.now().isoformat(), 1))
    conn.commit()
    conn.close()

def log_action(user_id, action, ip):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, action, ip, created) VALUES (?, ?, ?, ?)",
              (user_id, action, ip, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;text-align:center;padding:50px;}
input{background:#222;color:#0f0;border:1px solid #0f0;padding:10px;margin:10px;width:200px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}</style>
</head>
<body>
<h1>MONEYMOM</h1>
<h2>Premium Bills Supply - BIF 10,000</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Login</button>
</form>
<a href="/register" style="color:#0f0;">Register</a>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom - Register</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;text-align:center;padding:50px;}
input{background:#222;color:#0f0;border:1px solid #0f0;padding:10px;margin:10px;width:200px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}</style>
</head>
<body>
<h1>Register</h1>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Create Account</button>
</form>
<a href="/login">Back to Login</a>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% if success %}<p style="color:#0f0;">{{ success }}</p>{% endif %}
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px;}
.note{border:1px solid #0f0;margin:20px 0;padding:10px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;}</style>
</head>
<body>
<h1>MoneyMom</h1>
<p>Welcome, {{ username }}</p>
<form method="POST" action="/generate"><button type="submit">GENERATE BIF 10,000 NOTE</button></form>
<h2>Your Notes</h2>
{% for note in notes %}
<div class="note">
<p>Note ID: {{ note.0 }}</p>
<p>Created: {{ note.5 }}</p>
<a href="/view/{{ note.0 }}">View Note (Front & Back)</a> | 
<a href="/download/{{ note.0 }}">Download as PNG</a>
</div>
{% endfor %}
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom Admin</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #0f0;padding:8px;}</style>
</head>
<body>
<h1>Admin Panel</h1>
<h2>Users</h2>
<table><tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
{% for u in users %}<tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{{ u.4 }}</td></tr>{% endfor %}
</table>
<h2>Generated Notes</h2>
<table><tr><th>ID</th><th>User ID</th><th>Created</th></tr>
{% for n in notes %}<tr><td>{{ n.0 }}</td><td>{{ n.1 }}</td><td>{{ n.5 }}</td></tr>{% endfor %}
</table>
<h2>Logs</h2>
<table><tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
{% for l in logs %}<tr><td>{{ l.4 }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>{% endfor %}
</table>
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password, is_admin FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            log_action(user[0], "Login", request.remote_addr)
            if user[3] == 1:
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        error = "Invalid credentials"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        hashed = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                      (username, hashed, request.remote_addr, datetime.datetime.now().isoformat(), 0))
            conn.commit()
            return render_template_string(REGISTER_TEMPLATE, success="Account created! Please login.")
        except:
            return render_template_string(REGISTER_TEMPLATE, error="Username exists")
        finally:
            conn.close()
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created DESC", (session['user_id'],))
    notes = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], notes=notes)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    serial = f"EJ{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, serial_number, front_img, back_img, created) VALUES (?, ?, ?, ?, ?)",
              (user_id, serial, FRONT_IMG_BASE64, BACK_IMG_BASE64, datetime.datetime.now().isoformat()))
    note_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_action(user_id, f"Generated note: {serial}", request.remote_addr)
    return redirect(url_for('dashboard'))

@app.route('/view/<int:note_id>')
@login_required
def view_note(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT front_img, back_img, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    if note and note[2] == session['user_id']:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>BIF 10,000 Note</title>
        <style>body{{background:#333;display:flex;flex-direction:column;align-items:center;padding:20px;}}
        img{{max-width:90%;margin:10px;border:1px solid gold;}}</style>
        </head>
        <body>
        <h1 style="color:#0f0;">BIF 10,000 Francs</h1>
        <img src="data:image/jpeg;base64,{note[0]}"><br>
        <img src="data:image/jpeg;base64,{note[1]}">
        <p><a href="/dashboard">Back</a></p>
        </body>
        </html>
        '''
    return "Not found", 404

@app.route('/download/<int:note_id>')
@login_required
def download(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT front_img, back_img, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    if note and note[2] == session['user_id']:
        from PIL import Image
        import base64
        front = Image.open(io.BytesIO(base64.b64decode(note[0])))
        back = Image.open(io.BytesIO(base64.b64decode(note[1])))
        total_width = front.width * 2
        combined = Image.new('RGB', (total_width, front.height))
        combined.paste(front, (0, 0))
        combined.paste(back, (front.width, 0))
        buffered = io.BytesIO()
        combined.save(buffered, format="PNG")
        return send_file(io.BytesIO(buffered.getvalue()), mimetype='image/png', as_attachment=True, download_name=f'BIF_10000_{note_id}.png')
    return "Not found", 404

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    notes = c.execute("SELECT * FROM notes ORDER BY created DESC LIMIT 100").fetchall()
    logs = c.execute("SELECT * FROM logs ORDER BY created DESC LIMIT 200").fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, users=users, notes=notes, logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("MoneyMom RUNNING with REAL note images")
    print("Admin: Mpc / 08800Mpc+_+")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
