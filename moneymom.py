#!/usr/bin/env python3
"""
MoneyMom - Advanced BIF 10,000 Counterfeit Note Generator
Authorized Government Use Only - Burundi Movement
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import hashlib
import uuid
import datetime
import os
import secrets
import base64
import time
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=24)

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
    
    # Create admin user if not exists
    admin_pass = generate_password_hash("08800Mpc+_+")
    c.execute("SELECT * FROM users WHERE username=?", ("Mpc",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ("Mpc", admin_pass, "0.0.0.0", datetime.datetime.now().isoformat(), 1))
    
    conn.commit()
    conn.close()

# Generate forensic serial number
def generate_serial(user_id):
    timestamp = hex(int(time.time()))[2:]
    forensic = f"BRB{str(user_id).zfill(4)}{timestamp}"
    return forensic[:20]

# Generate BIF 10,000 note image - Advanced
def create_note_image(serial, user_id, username):
    # Dimensions: 144x72mm at 200dpi = 1134x567px
    width = 1134
    height = 567
    
    # Create image with light yellow background
    img = Image.new('RGB', (width, height), color=(253, 242, 181))
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts, use default if not available
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Background pattern - subtle lines
    for y in range(0, height, 20):
        draw.line([(0, y), (width, y)], fill=(230, 220, 160), width=1)
    
    # Border frame
    draw.rectangle([(10, 10), (width-10, height-10)], outline=(139, 69, 19), width=3)
    draw.rectangle([(15, 15), (width-15, height-15)], outline=(139, 69, 19), width=1)
    
    # Draw denomination
    draw.text((60, 120), "10,000", fill=(0, 0, 0), font=font_large)
    draw.text((880, 120), "DIX MILLE", fill=(0, 0, 0), font=font_large)
    
    # Draw serial number
    draw.text((60, 480), f"Serial: {serial}", fill=(0, 0, 0), font=font_small)
    
    # Decorative center box
    draw.rectangle([(350, 160), (784, 380)], outline=(139, 69, 19), width=2)
    draw.rectangle([(355, 165), (779, 375)], outline=(139, 69, 19), width=1)
    
    # Center text
    draw.text((440, 200), "BANQUE DE LA REPUBLIQUE", fill=(0, 0, 0), font=font_medium)
    draw.text((490, 240), "DU BURUNDI", fill=(0, 0, 0), font=font_medium)
    draw.text((440, 290), "10000 FRANCS", fill=(139, 0, 0), font=font_large)
    
    # Hippopotamus silhouette
    draw.ellipse([(900, 420), (1050, 520)], outline=(100, 100, 100), width=2)
    draw.ellipse([(920, 430), (980, 480)], fill=(50, 50, 50))
    
    # Add invisible forensic microprint (visible under magnification)
    forensic = f"GOV-BDI-OP-{user_id}-{username}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    for i, char in enumerate(forensic[:100]):
        draw.text((400 + i*3, 540), char, fill=(253, 242, 181), font=font_tiny)
    
    # Add UV reactive elements (simulated - will look dark but under UV would glow)
    uv_text = "BURUNDI"
    for i, char in enumerate(uv_text):
        draw.text((200 + i*15, 300), char, fill=(200, 180, 100), font=font_medium)
    
    return img

# Logging function
def log_action(user_id, action, ip):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, action, ip, created) VALUES (?, ?, ?, ?)",
              (user_id, action, ip, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Login required decorator
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
        input:focus { outline: none; border-color: #ff00ff; box-shadow: 0 0 10px rgba(255, 0, 255, 0.3); }
        button { width: 100%; padding: 12px; background: #00ff41; color: #000; border: none; font-size: 16px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-top: 10px; transition: all 0.3s; }
        button:hover { background: #ff00ff; color: #fff; box-shadow: 0 0 20px rgba(255, 0, 255, 0.5); }
        a { color: #00ff41; text-decoration: none; display: block; text-align: center; margin-top: 20px; }
        a:hover { color: #ff00ff; }
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
        .container { background: rgba(0, 0, 0, 0.85); border-radius: 20px; padding: 40px; width: 400px; border: 1px solid #00ff41; box-shadow: 0 0 30px rgba(0, 255, 65, 0.2); }
        h1 { color: #00ff41; text-align: center; font-size: 32px; margin-bottom: 30px; letter-spacing: 5px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #0a0a0a; border: 1px solid #00ff41; color: #00ff41; font-family: monospace; font-size: 14px; border-radius: 5px; }
        input:focus { outline: none; border-color: #ff00ff; }
        button { width: 100%; padding: 12px; background: #00ff41; color: #000; border: none; font-size: 16px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-top: 10px; }
        button:hover { background: #ff00ff; color: #fff; }
        a { color: #00ff41; text-decoration: none; display: block; text-align: center; margin-top: 20px; }
        .error { color: #ff4444; text-align: center; margin-top: 10px; }
        .success { color: #00ff41; text-align: center; margin-top: 10px; }
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
        .logo { color: #00ff41; font-size: 24px; font-weight: bold; letter-spacing: 3px; }
        .user { color: #00ff41; }
        .logout { color: #ff4444; text-decoration: none; margin-left: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .generate-box { background: rgba(0, 0, 0, 0.85); border: 1px solid #00ff41; border-radius: 10px; padding: 30px; text-align: center; margin-bottom: 30px; }
        .generate-btn { background: #00ff41; color: #000; padding: 15px 40px; font-size: 18px; font-weight: bold; border: none; cursor: pointer; border-radius: 5px; transition: all 0.3s; }
        .generate-btn:hover { background: #ff00ff; color: #fff; box-shadow: 0 0 20px rgba(255, 0, 255, 0.5); }
        .notes-list { background: rgba(0, 0, 0, 0.85); border: 1px solid #00ff41; border-radius: 10px; padding: 20px; }
        .note-item { border-bottom: 1px solid #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .note-item:last-child { border-bottom: none; }
        .note-serial { color: #00ff41; font-family: monospace; }
        .note-date { color: #888; font-size: 12px; }
        .note-actions a { color: #00ff41; text-decoration: none; margin-left: 15px; }
        .note-actions a:hover { color: #ff00ff; }
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
            <div style="color: #888; text-align: center; padding: 40px;">No notes generated yet. Click GENERATE above.</div>
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
    <title>MoneyMom | Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); font-family: 'Courier New', monospace; padding: 20px; }
        .header { background: rgba(0, 0, 0, 0.85); border-bottom: 1px solid #ff00ff; padding: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
        .logo { color: #ff00ff; font-size: 24px; font-weight: bold; letter-spacing: 3px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .section { background: rgba(0, 0, 0, 0.85); border: 1px solid #ff00ff; border-radius: 10px; padding: 20px; margin-bottom: 30px; }
        h2 { color: #ff00ff; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #333; padding: 10px; text-align: left; color: #00ff41; }
        th { background: rgba(255, 0, 255, 0.2); color: #ff00ff; }
        .badge { color: #ff00ff; font-weight: bold; }
        .logout { color: #ff4444; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">MONEYMOM | ADMIN</div>
        <div><a href="/logout" class="logout">[EXIT]</a></div>
    </div>
    <div class="container">
        <div class="section">
            <h2>👥 USERS ({{ users|length }})</h2>
            <table>
                <tr><th>ID</th><th>Username</th><th>IP</th><th>Admin</th><th>Created</th></tr>
                {% for u in users %}
                <tr>
                    <td>{{ u.0 }}</td>
                    <td>{{ u.1 }}</td>
                    <td>{{ u.3 }}</td>
                    <td>{% if u.6 == 1 %}✅{% else %}❌{% endif %}</td>
                    <td>{{ u.4 }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <div class="section">
            <h2>💰 GENERATED NOTES ({{ notes|length }})</h2>
            <table>
                <tr><th>ID</th><th>User ID</th><th>Serial</th><th>Created</th></tr>
                {% for n in notes %}
                <tr>
                    <td>{{ n.0 }}</td>
                    <td>{{ n.1 }}</td>
                    <td>{{ n.2 }}</td>
                    <td>{{ n.4 }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <div class="section">
            <h2>📜 ACTIVITY LOGS ({{ logs|length }})</h2>
            <table>
                <tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
                {% for l in logs %}
                <tr>
                    <td>{{ l.4 }}</td>
                    <td>{{ l.1 }}</td>
                    <td>{{ l.2 }}</td>
                    <td>{{ l.3 }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
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
            log_action(user[0], f"Login from {request.remote_addr}", request.remote_addr)
            
            if user[3] == 1:
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials"
    
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(username) < 3:
            error = "Username too short"
        elif len(password) < 4:
            error = "Password too short"
        else:
            conn = sqlite3.connect('moneymom.db')
            c = conn.cursor()
            hashed = generate_password_hash(password)
            try:
                c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                          (username, hashed, request.remote_addr, datetime.datetime.now().isoformat(), 0))
                conn.commit()
                success = "Account created! Please login."
                log_action(None, f"New user: {username}", request.remote_addr)
            except sqlite3.IntegrityError:
                error = "Username already exists"
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
    
    log_action(user_id, f"Generated note: {serial}", request.remote_addr)
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
