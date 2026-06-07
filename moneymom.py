#!/usr/bin/env python3
"""
MoneyMom - Real BIF 10,000 Counterfeit Note Generator
Authorized Government Use Only - Burundi Movement
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import hashlib
import datetime
import os
import secrets
import base64
import time
import random
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Database setup
def init_db():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  ip TEXT, 
                  created TEXT,
                  is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  serial_number TEXT UNIQUE,
                  image_blob TEXT,
                  created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  action TEXT,
                  ip TEXT,
                  created TEXT)''')
    
    # Create admin user
    admin_pass = generate_password_hash("08800Mpc+_+")
    c.execute("SELECT * FROM users WHERE username=?", ("Mpc",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ("Mpc", admin_pass, "0.0.0.0", datetime.datetime.now().isoformat(), 1))
    
    conn.commit()
    conn.close()

# Generate realistic serial number matching real BIF format
def generate_serial(user_id):
    # Format: EJ + 6 digits + year (like EJ6272023 from your image)
    year = datetime.datetime.now().year
    digits = str(random.randint(100000, 999999))
    serial = f"EJ{digits}{year}"
    return serial[:15]

# Create note using real templates
def create_note_image(serial, user_id, username):
    # Load real templates
    front_path = "bif_front.jpg"
    back_path = "bif_back.jpg"
    
    # If files don't exist, use fallback
    if not os.path.exists(front_path):
        front = Image.new('RGB', (800, 400), color=(200, 180, 100))
    else:
        front = Image.open(front_path)
        front = front.convert('RGB')
    
    if not os.path.exists(back_path):
        back = Image.new('RGB', (800, 400), color=(180, 160, 80))
    else:
        back = Image.open(back_path)
        back = back.convert('RGB')
    
    # Resize to reasonable dimensions
    front = front.resize((850, 400))
    back = back.resize((850, 400))
    
    # Add serial number to front
    draw_front = ImageDraw.Draw(front)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    # Position serial where it appears on real note (adjust as needed)
    draw_front.text((270, 330), serial, fill=(0, 0, 0), font=font)
    
    # Add invisible forensic marker (for tracking)
    forensic = f"GOV-BDI-{user_id}-{username}-{int(time.time())}"
    forensic_font = ImageFont.load_default()
    draw_front.text((5, 5), forensic, fill=(245, 235, 175), font=forensic_font)
    
    # Combine front and back vertically (front on top, back below)
    total_height = front.height + back.height
    combined = Image.new('RGB', (front.width, total_height), (255, 255, 255))
    combined.paste(front, (0, 0))
    combined.paste(back, (0, front.height))
    
    return combined

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
<head>
    <title>MoneyMom | Premium Bills Supply</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); font-family: 'Courier New', monospace; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { background: rgba(0, 0, 0, 0.85); border-radius: 20px; padding: 40px; width: 400px; border: 1px solid #00ff41; box-shadow: 0 0 30px rgba(0, 255, 65, 0.2); }
        h1 { color: #00ff41; text-align: center; font-size: 32px; margin-bottom: 10px; letter-spacing: 5px; }
        .sub { color: #00ff41; text-align: center; font-size: 12px; margin-bottom: 30px; opacity: 0.7; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0a0a0a; border: 1px solid #00ff41; color: #00ff41; font-family: monospace; font-size: 14px; border-radius: 5px; }
        input:focus { outline: none; border-color: #ff00ff; }
        button { width: 100%; padding: 12px; background: #00ff41; color: #000; border: none; font-size: 16px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-top: 10px; }
        button:hover { background: #ff00ff; color: #fff; }
        a { color: #00ff41; text-decoration: none; display: block; text-align: center; margin-top: 20px; }
        .error { color: #ff4444; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MONEYMOM</h1>
        <div class="sub">Premium Bills Supply</div>
        <form method="POST">
            <input type="text" name="username" placeholder="USERNAME" required>
            <input type="password" name="password" placeholder="PASSWORD" required>
            <button type="submit">ACCESS</button>
        </form>
        <a href="/register">[ NO ACCOUNT? REGISTER ]</a>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Register</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); font-family: 'Courier New', monospace; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { background: rgba(0, 0, 0, 0.85); border-radius: 20px; padding: 40px; width: 400px; border: 1px solid #00ff41; }
        h1 { color: #00ff41; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0a0a0a; border: 1px solid #00ff41; color: #00ff41; }
        button { width: 100%; padding: 12px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; }
        a { color: #00ff41; text-decoration: none; display: block; text-align: center; margin-top: 20px; }
        .error { color: #ff4444; text-align: center; }
        .success { color: #00ff41; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>REGISTER</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="USERNAME" required>
            <input type="password" name="password" placeholder="PASSWORD" required>
            <button type="submit">CREATE ACCOUNT</button>
        </form>
        <a href="/login">[ BACK TO LOGIN ]</a>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if success %}<div class="success">{{ success }}</div>{% endif %}
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); font-family: 'Courier New', monospace; padding: 20px; }
        .header { background: rgba(0, 0, 0, 0.85); border-bottom: 1px solid #00ff41; padding: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
        .logo { color: #00ff41; font-size: 24px; font-weight: bold; }
        .user { color: #00ff41; }
        .logout { color: #ff4444; text-decoration: none; margin-left: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .generate-box { background: rgba(0, 0, 0, 0.85); border: 1px solid #00ff41; border-radius: 10px; padding: 30px; text-align: center; margin-bottom: 30px; }
        .generate-btn { background: #00ff41; color: #000; padding: 15px 40px; font-size: 18px; font-weight: bold; border: none; cursor: pointer; border-radius: 5px; }
        .generate-btn:hover { background: #ff00ff; color: #fff; }
        .notes-list { background: rgba(0, 0, 0, 0.85); border: 1px solid #00ff41; border-radius: 10px; padding: 20px; }
        .note-item { border-bottom: 1px solid #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .note-serial { color: #00ff41; }
        .note-date { color: #888; font-size: 12px; }
        .note-actions a { color: #00ff41; text-decoration: none; margin-left: 15px; }
        h2 { color: #00ff41; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">MONEYMOM</div>
        <div class="user">{{ username }} <a href="/logout" class="logout">[EXIT]</a></div>
    </div>
    <div class="container">
        <div class="generate-box">
            <form method="POST" action="/generate">
                <button type="submit" class="generate-btn">⚡ GENERATE 10,000 BIF NOTE ⚡</button>
            </form>
        </div>
        <div class="notes-list">
            <h2>📋 YOUR GENERATED NOTES</h2>
            {% for note in notes %}
            <div class="note-item">
                <div>
                    <div class="note-serial">🔹 SERIAL: {{ note.2 }}</div>
                    <div class="note-date">📅 {{ note.4 }}</div>
                </div>
                <div class="note-actions">
                    <a href="/view/{{ note.0 }}">👁️ VIEW</a>
                    <a href="/download/{{ note.0 }}">⬇️ DOWNLOAD</a>
                </div>
            </div>
            {% else %}
            <div style="color: #888; text-align: center; padding: 40px;">No notes generated yet.</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); font-family: 'Courier New', monospace; padding: 20px; }
        .header { background: rgba(0, 0, 0, 0.85); border-bottom: 1px solid #ff00ff; padding: 20px; margin-bottom: 30px; }
        .logo { color: #ff00ff; font-size: 24px; }
        .section { background: rgba(0, 0, 0, 0.85); border: 1px solid #ff00ff; border-radius: 10px; padding: 20px; margin-bottom: 30px; }
        h2 { color: #ff00ff; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #333; padding: 10px; text-align: left; color: #00ff41; }
        th { background: rgba(255, 0, 255, 0.2); color: #ff00ff; }
        .logout { color: #ff4444; text-decoration: none; float: right; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">MONEYMOM | ADMIN <a href="/logout" class="logout">[EXIT]</a></div>
    </div>
    <div class="section">
        <h2>👥 USERS</h2>
        <table> <tr><th>ID</th><th>Username</th><th>IP</th><th>Admin</th><th>Created</th></tr>
        {% for u in users %}
        <tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{% if u.6 == 1 %}✅{% else %}❌{% endif %}</td><td>{{ u.4 }}</td></tr>
        {% endfor %}
        </table>
    </div>
    <div class="section">
        <h2>💰 NOTES</h2>
        <table> <tr><th>ID</th><th>User ID</th><th>Serial</th><th>Created</th></tr>
        {% for n in notes %}
        <tr><td>{{ n.0 }}</td><td>{{ n.1 }}</td><td>{{ n.2 }}</td><td>{{ n.4 }}</td></tr>
        {% endfor %}
        </table>
    </div>
    <div class="section">
        <h2>📜 LOGS</h2>
        <table> <tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
        {% for l in logs %}
        <tr><td>{{ l.4 }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>
        {% endfor %}
        </table>
    </div>
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
    error = None
    success = None
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
            success = "Account created! Please login."
        except:
            error = "Username exists"
        finally:
            conn.close()
    return render_template_string(REGISTER_TEMPLATE, error=error, success=success)

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
    username = session['username']
    serial = generate_serial(user_id)
    img = create_note_image(serial, user_id, username)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, serial_number, image_blob, created) VALUES (?, ?, ?, ?)",
              (user_id, serial, img_base64, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    log_action(user_id, f"Generated: {serial}", request.remote_addr)
    return redirect(url_for('dashboard'))

@app.route('/view/<int:note_id>')
@login_required
def view_note(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    if note and note[1] == session['user_id']:
        img_data = base64.b64decode(note[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png')
    return "Not found", 404

@app.route('/download/<int:note_id>')
@login_required
def download(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    if note and note[1] == session['user_id']:
        img_data = base64.b64decode(note[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'BIF_10000_{note_id}.png')
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
    if 'user_id' in session:
        log_action(session['user_id'], "Logout", request.remote_addr)
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
