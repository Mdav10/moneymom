#!/usr/bin/env python3
"""
MoneyMom Pro - Advanced BIF 10,000 Counterfeit Platform
Authorized Government Use Only - Burundi Movement
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for, jsonify
import io
import sqlite3
import datetime
import os
import secrets
import base64
import hashlib
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = datetime.timedelta(hours=24)

# Load real note images
try:
    with open('bif_front.jpg', 'rb') as f:
        FRONT_IMG_BASE64 = base64.b64encode(f.read()).decode()
    with open('bif_back.jpg', 'rb') as f:
        BACK_IMG_BASE64 = base64.b64encode(f.read()).decode()
except:
    FRONT_IMG_BASE64 = None
    BACK_IMG_BASE64 = None

def init_db():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  email TEXT,
                  wallet TEXT,
                  ip TEXT, 
                  created TEXT, 
                  last_login TEXT,
                  is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY, 
                  user_id INTEGER, 
                  serial_number TEXT UNIQUE, 
                  front_img TEXT, 
                  back_img TEXT, 
                  created TEXT,
                  status TEXT DEFAULT 'active')''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY, 
                  user_id INTEGER, 
                  action TEXT, 
                  ip TEXT, 
                  created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, 
                  user_id INTEGER, 
                  quantity INTEGER, 
                  total_amount INTEGER, 
                  payment_method TEXT,
                  status TEXT,
                  created TEXT)''')
    
    # Create admin user
    admin_pass = generate_password_hash("08800Mpc+_+")
    c.execute("SELECT * FROM users WHERE username=?", ("Mpc",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, email, wallet, ip, created, last_login, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ("Mpc", admin_pass, "admin@moneymom.bi", "BRB78901234", "0.0.0.0", datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat(), 1))
    
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

# ============ PROFESSIONAL HTML TEMPLATES ============

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyMom | Secure Bills Supply</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #0f1422 50%, #0a0e1a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow-x: hidden;
        }
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0,255,65,0.03) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .container {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 450px;
            padding: 20px;
        }
        .card {
            background: rgba(18, 22, 35, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 40px;
            border: 1px solid rgba(0, 255, 65, 0.2);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 255, 65, 0.1);
            transition: all 0.3s ease;
        }
        .card:hover {
            border-color: rgba(0, 255, 65, 0.4);
            box-shadow: 0 30px 60px -12px rgba(0, 255, 65, 0.15);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 42px;
            font-weight: 800;
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: 2px;
        }
        .logo p {
            color: #6b7280;
            font-size: 14px;
            margin-top: 8px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        .input-group label {
            display: block;
            color: #9ca3af;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .input-group input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(0, 255, 65, 0.2);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            transition: all 0.3s ease;
        }
        .input-group input:focus {
            outline: none;
            border-color: #00ff41;
            background: rgba(0, 0, 0, 0.6);
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.1);
        }
        .input-group input::placeholder {
            color: #4b5563;
        }
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%);
            border: none;
            border-radius: 12px;
            color: #000;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 255, 65, 0.3);
        }
        .links {
            text-align: center;
            margin-top: 24px;
        }
        .links a {
            color: #00ff41;
            text-decoration: none;
            font-size: 14px;
            transition: color 0.3s;
        }
        .links a:hover {
            color: #ff00ff;
        }
        .error {
            background: rgba(255, 68, 68, 0.1);
            border-left: 3px solid #ff4444;
            padding: 12px;
            border-radius: 8px;
            color: #ff8888;
            font-size: 13px;
            margin-bottom: 20px;
        }
        .features {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .feature {
            text-align: center;
            flex: 1;
        }
        .feature span {
            font-size: 20px;
            display: block;
            margin-bottom: 5px;
        }
        .feature p {
            color: #4b5563;
            font-size: 10px;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="container">
        <div class="card">
            <div class="logo">
                <h1>MONEYMOM</h1>
                <p>Premium Currency Supply</p>
            </div>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <div class="input-group">
                    <label>USERNAME</label>
                    <input type="text" name="username" placeholder="Enter your username" required>
                </div>
                <div class="input-group">
                    <label>PASSWORD</label>
                    <input type="password" name="password" placeholder="Enter your password" required>
                </div>
                <button type="submit" class="btn">🔓 ACCESS PLATFORM</button>
            </form>
            <div class="links">
                <a href="/register">No account? Register now →</a>
            </div>
            <div class="features">
                <div class="feature"><span>⚡</span><p>Instant Delivery</p></div>
                <div class="feature"><span>🔒</span><p>Secure</p></div>
                <div class="feature"><span>🌍</span><p>Worldwide</p></div>
            </div>
        </div>
    </div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyMom | Register</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #0f1422 50%, #0a0e1a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card {
            background: rgba(18, 22, 35, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 40px;
            border: 1px solid rgba(0, 255, 65, 0.2);
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; color: #9ca3af; font-size: 13px; margin-bottom: 8px; text-transform: uppercase; }
        .input-group input { width: 100%; padding: 14px 16px; background: rgba(0,0,0,0.4); border: 1px solid rgba(0,255,65,0.2); border-radius: 12px; color: #fff; }
        .input-group input:focus { outline: none; border-color: #00ff41; }
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%); border: none; border-radius: 12px; color: #000; font-weight: 700; cursor: pointer; }
        .links { text-align: center; margin-top: 24px; }
        .links a { color: #00ff41; text-decoration: none; }
        .error { background: rgba(255,68,68,0.1); border-left: 3px solid #ff4444; padding: 12px; border-radius: 8px; color: #ff8888; margin-bottom: 20px; }
        .success { background: rgba(0,255,65,0.1); border-left: 3px solid #00ff41; padding: 12px; border-radius: 8px; color: #00ff88; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo"><h1>CREATE ACCOUNT</h1></div>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success">{{ success }}</div>{% endif %}
            <form method="POST">
                <div class="input-group"><label>USERNAME</label><input type="text" name="username" placeholder="Choose username" required></div>
                <div class="input-group"><label>EMAIL (OPTIONAL)</label><input type="email" name="email" placeholder="your@email.com"></div>
                <div class="input-group"><label>PASSWORD</label><input type="password" name="password" placeholder="Create password" required></div>
                <div class="input-group"><label>CONFIRM PASSWORD</label><input type="password" name="confirm" placeholder="Confirm password" required></div>
                <button type="submit" class="btn">✅ REGISTER</button>
            </form>
            <div class="links"><a href="/login">← Back to Login</a></div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyMom | Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0e1a;
            color: #fff;
        }
        .header {
            background: rgba(18, 22, 35, 0.95);
            border-bottom: 1px solid rgba(0, 255, 65, 0.2);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .logo h1 {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .user-info span {
            color: #00ff41;
            font-weight: 600;
        }
        .logout-btn {
            background: rgba(255,68,68,0.2);
            padding: 8px 16px;
            border-radius: 8px;
            color: #ff6666;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s;
        }
        .logout-btn:hover {
            background: rgba(255,68,68,0.4);
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(18, 22, 35, 0.8);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(0, 255, 65, 0.1);
            text-align: center;
        }
        .stat-card h3 { color: #6b7280; font-size: 13px; text-transform: uppercase; margin-bottom: 10px; }
        .stat-card .value { font-size: 32px; font-weight: 700; color: #00ff41; }
        .generate-section {
            background: linear-gradient(135deg, rgba(0,255,65,0.05) 0%, rgba(0,204,51,0.02) 100%);
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            border: 1px solid rgba(0, 255, 65, 0.2);
            margin-bottom: 40px;
        }
        .generate-btn {
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%);
            color: #000;
            font-size: 20px;
            font-weight: 700;
            padding: 16px 48px;
            border: none;
            border-radius: 48px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .generate-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 40px rgba(0, 255, 65, 0.3);
        }
        .notes-section {
            background: rgba(18, 22, 35, 0.6);
            border-radius: 24px;
            padding: 30px;
            border: 1px solid rgba(0, 255, 65, 0.1);
        }
        .notes-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .notes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .note-card {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(0, 255, 65, 0.15);
            transition: all 0.3s;
        }
        .note-card:hover {
            border-color: rgba(0, 255, 65, 0.4);
            transform: translateY(-2px);
        }
        .note-id { color: #00ff41; font-size: 12px; font-family: monospace; margin-bottom: 8px; }
        .note-date { color: #6b7280; font-size: 11px; margin-bottom: 15px; }
        .note-actions { display: flex; gap: 15px; margin-top: 15px; }
        .note-actions a {
            color: #00ff41;
            text-decoration: none;
            font-size: 13px;
            transition: color 0.3s;
        }
        .note-actions a:hover { color: #ff00ff; }
        .empty-state {
            text-align: center;
            padding: 60px;
            color: #6b7280;
        }
        @media (max-width: 768px) {
            .header { padding: 15px 20px; }
            .container { padding: 20px; }
            .generate-btn { font-size: 16px; padding: 12px 32px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><h1>⚡ MONEYMOM</h1></div>
        <div class="user-info">
            <span>👤 {{ username }}</span>
            <a href="/logout" class="logout-btn">🚪 EXIT</a>
        </div>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat-card"><h3>Total Notes</h3><div class="value">{{ notes_count }}</div></div>
            <div class="stat-card"><h3>Member Since</h3><div class="value" style="font-size: 16px;">{{ member_since }}</div></div>
        </div>
        <div class="generate-section">
            <form method="POST" action="/generate">
                <button type="submit" class="generate-btn">💰 GENERATE 10,000 BIF NOTE 💰</button>
            </form>
            <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">High quality • Instant delivery • Untraceable</p>
        </div>
        <div class="notes-section">
            <div class="notes-header">
                <h3>📋 YOUR GENERATED NOTES</h3>
                <span style="color: #6b7280; font-size: 12px;">{{ notes|length }} notes</span>
            </div>
            <div class="notes-grid">
                {% for note in notes %}
                <div class="note-card">
                    <div class="note-id">🔹 ID: {{ note.0 }}</div>
                    <div class="note-date">📅 {{ note.5[:16] }}</div>
                    <div class="note-actions">
                        <a href="/view/{{ note.0 }}" target="_blank">👁️ View Note</a>
                        <a href="/download/{{ note.0 }}">⬇️ Download PNG</a>
                    </div>
                </div>
                {% else %}
                <div class="empty-state">
                    <p>No notes generated yet.</p>
                    <p style="font-size: 12px;">Click the button above to generate your first BIF 10,000 note.</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyMom | Admin Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0e1a; color: #fff; }
        .header { background: rgba(18,22,35,0.95); border-bottom: 1px solid rgba(255,0,255,0.3); padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; }
        .logo h1 { font-size: 28px; color: #ff00ff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .section { background: rgba(18,22,35,0.6); border-radius: 16px; padding: 25px; margin-bottom: 30px; border: 1px solid rgba(255,0,255,0.1); }
        .section h2 { color: #ff00ff; margin-bottom: 20px; font-size: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: #ff00ff; font-size: 12px; text-transform: uppercase; }
        td { color: #9ca3af; font-size: 13px; }
        .badge { color: #00ff41; }
        .logout-btn { color: #ff4444; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><h1>🔐 MONEYMOM | ADMIN</h1></div>
        <a href="/logout" class="logout-btn">🚪 EXIT</a>
    </div>
    <div class="container">
        <div class="section">
            <h2>👥 USERS ({{ users|length }})</h2>
            <table>
                <tr><th>ID</th><th>Username</th><th>Email</th><th>IP</th><th>Created</th><th>Admin</th></tr>
                {% for u in users %}
                <tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 or '-' }}</td><td>{{ u.5 }}</td><td>{{ u.6[:10] }}</td><td>{% if u.9 == 1 %}✅{% else %}❌{% endif %}</td></tr>
                {% endfor %}
            </table>
        </div>
        <div class="section">
            <h2>💰 NOTES ({{ notes|length }})</h2>
            <table>
                <tr><th>ID</th><th>User ID</th><th>Serial</th><th>Created</th></tr>
                {% for n in notes %}
                <tr><td>{{ n.0 }}</td><td>{{ n.1 }}</td><td class="badge">{{ n.2 }}</td><td>{{ n.5[:16] }}</td></tr>
                {% endfor %}
            </table>
        </div>
        <div class="section">
            <h2>📜 LOGS ({{ logs|length }})</h2>
            <table>
                <tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
                {% for l in logs %}
                <tr><td>{{ l.4[:16] }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
'''

# ============ ROUTES ============

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
            session.permanent = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            # Update last login
            conn = sqlite3.connect('moneymom.db')
            c = conn.cursor()
            c.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now().isoformat(), user[0]))
            conn.commit()
            conn.close()
            log_action(user[0], f"Login from {request.remote_addr}", request.remote_addr)
            if user[3] == 1:
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        error = "Invalid username or password"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form.get('confirm', '')
        email = request.form.get('email', '')
        
        if password != confirm:
            return render_template_string(REGISTER_TEMPLATE, error="Passwords do not match")
        if len(password) < 6:
            return render_template_string(REGISTER_TEMPLATE, error="Password must be at least 6 characters")
        
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        hashed = generate_password_hash(password)
        wallet = f"BRB{secrets.token_hex(4).upper()}"
        try:
            c.execute("INSERT INTO users (username, password, email, wallet, ip, created, last_login, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (username, hashed, email, wallet, request.remote_addr, datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat(), 0))
            conn.commit()
            log_action(None, f"New registration: {username}", request.remote_addr)
            return render_template_string(REGISTER_TEMPLATE, success="Account created! Please login.")
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_TEMPLATE, error="Username already exists")
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
    c.execute("SELECT created FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    member_since = user[0][:10] if user else "Unknown"
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], notes=notes, notes_count=len(notes), member_since=member_since)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    serial = f"EJ{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
    
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, serial_number, front_img, back_img, created, status) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, serial, FRONT_IMG_BASE64, BACK_IMG_BASE64, datetime.datetime.now().isoformat(), 'active'))
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
        <style>body{{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;padding:40px;}}
        img{{max-width:90%;margin:10px;border:1px solid #00ff41;border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,0.5);}}</style>
        </head>
        <body>
        <h1 style="color:#00ff41;">BIF 10,000 Francs</h1>
        <img src="data:image/jpeg;base64,{note[0]}">
        <img src="data:image/jpeg;base64,{note[1]}">
        <p style="color:#fff;"><a href="/dashboard" style="color:#00ff41;">← Back to Dashboard</a></p>
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
        front = Image.open(io.BytesIO(base64.b64decode(note[0])))
        back = Image.open(io.BytesIO(base64.b64decode(note[1])))
        total_width = front.width * 2
        combined = Image.new('RGB', (total_width, front.height))
        combined.paste(front, (0, 0))
        combined.paste(back, (front.width, 0))
        buffered = io.BytesIO()
        combined.save(buffered, format="PNG", quality=95)
        return send_file(io.BytesIO(buffered.getvalue()), mimetype='image/png', as_attachment=True, download_name=f'BIF_10000_{note_id}.png')
    return "Not found", 404

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    users = c.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
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
    print("="*60)
    print("🚀 MONEYMOM PRO - PROFESSIONAL PLATFORM")
    print(f"📍 Running on: http://localhost:{port}")
    print("👑 Admin: Mpc / 08800Mpc+_+")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)
