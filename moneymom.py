#!/usr/bin/env python3
"""
MoneyMom - BIF 10,000 Counterfeit Note Generator
Authorized Government Use Only - Burundi Movement
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import hashlib
import uuid
import datetime
import os
import secrets
from functools import wraps

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
                  created TEXT)''')
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
    conn.commit()
    conn.close()

# Create forensic serial number
def generate_serial(user_id):
    import time
    forensic = f"BRB{str(user_id).zfill(4)}{hex(int(time.time()))[2:]}"
    return forensic[:20]

# Generate BIF 10,000 note image
def create_note_image(serial, user_id):
    # Dimensions: 144x72mm at 150dpi = 850x425px
    width = 850
    height = 425
    
    # Create image with light yellow background
    img = Image.new('RGB', (width, height), color=(255, 235, 180))
    draw = ImageDraw.Draw(img)
    
    # Try to load font, use default if not available
    try:
        font_large = ImageFont.truetype("/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_small = ImageFont.truetype("/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_tiny = ImageFont.truetype("/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Draw denomination
    draw.text((50, 100), "10,000", fill=(0, 0, 0), font=font_large)
    draw.text((620, 100), "DIX MILLE", fill=(0, 0, 0), font=font_large)
    
    # Draw serial number
    draw.text((50, 350), serial, fill=(0, 0, 0), font=font_small)
    
    # Draw decorative rectangle
    draw.rectangle([(300, 150), (550, 280)], outline=(139, 69, 19), width=2)
    
    # Draw text
    draw.text((320, 180), "BANQUE DE LA REPUBLIQUE", fill=(0, 0, 0), font=font_small)
    draw.text((340, 210), "DU BURUNDI", fill=(0, 0, 0), font=font_small)
    draw.text((350, 240), "10000 FRANCS", fill=(0, 0, 0), font=font_small)
    
    # Draw "hippopotamus" shape (simplified)
    draw.ellipse([(700, 300), (800, 380)], outline=(100, 100, 100), width=1)
    
    # Add invisible forensic microprint (visible under magnification)
    forensic = f"GOV-BDI-OP-{user_id}-{datetime.datetime.now().strftime('%Y%m%d')}"
    for i, char in enumerate(forensic):
        draw.text((400 + i*3, 400), char, fill=(255, 235, 180), font=font_tiny)
    
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

# HTML templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom - Login</title>
    <style>
        body { background: #0a0a0a; color: #0f0; font-family: monospace; text-align: center; padding: 50px; }
        input { background: #222; color: #0f0; border: 1px solid #0f0; padding: 10px; margin: 10px; width: 200px; }
        button { background: #0f0; color: #000; padding: 10px 20px; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>MoneyMom</h1>
    <h2>Premium Bills Supply</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
    <p><a href="/register" style="color:#0f0;">Register</a></p>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom - Register</title>
    <style>
        body { background: #0a0a0a; color: #0f0; font-family: monospace; text-align: center; padding: 50px; }
        input { background: #222; color: #0f0; border: 1px solid #0f0; padding: 10px; margin: 10px; width: 200px; }
        button { background: #0f0; color: #000; padding: 10px 20px; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Register</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Register</button>
    </form>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom - Dashboard</title>
    <style>
        body { background: #0a0a0a; color: #0f0; font-family: monospace; padding: 20px; }
        .note { border: 1px solid #0f0; margin: 20px 0; padding: 10px; }
        button { background: #0f0; color: #000; padding: 10px 20px; border: none; cursor: pointer; }
        a { color: #0f0; }
    </style>
</head>
<body>
    <h1>MoneyMom - Dashboard</h1>
    <p>Welcome, {{ username }}</p>
    <form method="POST" action="/generate">
        <button type="submit">Generate New 10,000 BIF Note</button>
    </form>
    
    <h2>Your Generated Notes</h2>
    {% for note in notes %}
    <div class="note">
        <p>Serial: {{ note.serial }}</p>
        <p>Created: {{ note.created }}</p>
        <a href="/download/{{ note.id }}">Download Image</a>
    </div>
    {% endfor %}
    
    <p><a href="/logout">Logout</a></p>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom - Admin</title>
    <style>
        body { background: #0a0a0a; color: #0f0; font-family: monospace; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #0f0; padding: 8px; text-align: left; }
        th { background: #1a1a1a; }
    </style>
</head>
<body>
    <h1>Admin Panel</h1>
    
    <h2>Users</h2>
    <table>
        <tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
        {% for user in users %}
        <tr><td>{{ user.0 }}</td><td>{{ user.1 }}</td><td>{{ user.3 }}</td><td>{{ user.4 }}</td></tr>
        {% endfor %}
    </table>
    
    <h2>Generated Notes</h2>
    <table>
        <tr><th>ID</th><th>User ID</th><th>Serial</th><th>Created</th></tr>
        {% for note in notes %}
        <tr><td>{{ note.0 }}</td><td>{{ note.1 }}</td><td>{{ note.2 }}</td><td>{{ note.4 }}</td></tr>
        {% endfor %}
    </table>
    
    <h2>Logs</h2>
    <table>
        <tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
        {% for log in logs %}
        <tr><td>{{ log.4 }}</td><td>{{ log.1 }}</td><td>{{ log.2 }}</td><td>{{ log.3 }}</td></tr>
        {% endfor %}
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
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            log_action(user[0], "Login", request.remote_addr)
            if username == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        ip = request.remote_addr
        created = datetime.datetime.now().isoformat()
        
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, ip, created) VALUES (?, ?, ?, ?)",
                      (username, password, ip, created))
            conn.commit()
            log_action(None, f"New user registered: {username}", ip)
        except:
            return "Username exists"
        finally:
            conn.close()
        return redirect(url_for('login'))
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT id, serial_number, created FROM notes WHERE user_id=? ORDER BY created DESC", 
              (session['user_id'],))
    notes = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], notes=notes)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    serial = generate_serial(user_id)
    img = create_note_image(serial, user_id)
    
    # Convert image to base64 for storage
    import base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, serial_number, image_blob, created) VALUES (?, ?, ?, ?)",
              (user_id, serial, img_base64, datetime.datetime.now().isoformat()))
    note_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_action(user_id, f"Generated note: {serial}", request.remote_addr)
    return redirect(url_for('dashboard'))

@app.route('/download/<int:note_id>')
@login_required
def download(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    
    if note and note[1] == session['user_id']:
        import base64
        img_data = base64.b64decode(note[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'note_{note_id}.png')
    return "Not found"

@app.route('/admin')
@login_required
def admin():
    if session['username'] != 'admin':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    notes = c.execute("SELECT * FROM notes ORDER BY created DESC LIMIT 50").fetchall()
    logs = c.execute("SELECT * FROM logs ORDER BY created DESC LIMIL 100").fetchall()
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
    # Create admin user if not exists
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, ip, created) VALUES (?, ?, ?, ?)",
              ("admin", admin_pass, "127.0.0.1", datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    print("="*50)
    print("MoneyMom Running on Termux")
    print("Access from browser: http://localhost:5000")
    print("Admin login: admin / admin123")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)
