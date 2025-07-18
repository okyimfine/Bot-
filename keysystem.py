
from flask import Flask, render_template_string, request, jsonify, session
from database import db
import secrets
import string
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'keysystem_secret_2025'

# Admin credentials for key system
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "keysystem123"

KEY_SYSTEM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HackHub Key System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #2d3748;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            color: white;
            font-size: 1.875rem;
            font-weight: 700;
        }

        .logout-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .nav-tabs {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            margin-bottom: 2rem;
            overflow: hidden;
        }

        .nav-tab {
            flex: 1;
            padding: 1.25rem 2rem;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            color: #718096;
            transition: all 0.3s ease;
            text-align: center;
        }

        .nav-tab.active {
            color: #667eea;
            background: #f7fafc;
        }

        .nav-tab:hover {
            color: #667eea;
            background: #f7fafc;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }

        .card h2 {
            color: #2d3748;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f7fafc;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            color: #718096;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.5px;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            color: #2d3748;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 0.875rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #f7fafc;
        }

        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.875rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .btn-danger {
            background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
        }

        .btn-danger:hover {
            box-shadow: 0 10px 25px rgba(229, 62, 62, 0.3);
        }

        .key-item {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .key-info {
            flex: 1;
        }

        .key-code {
            font-family: 'Courier New', monospace;
            background: #2d3748;
            color: #f7fafc;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            display: inline-block;
        }

        .key-meta {
            font-size: 0.875rem;
            color: #718096;
        }

        .key-actions {
            display: flex;
            gap: 0.5rem;
        }

        .btn-sm {
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
        }

        .task-item {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .task-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 1rem;
        }

        .task-description {
            color: #718096;
            margin-bottom: 1rem;
            line-height: 1.6;
        }

        .task-reward {
            background: #48bb78;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
        }

        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-weight: 500;
        }

        .alert-success {
            background: #c6f6d5;
            color: #22543d;
            border: 1px solid #9ae6b4;
        }

        .alert-error {
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #feb2b2;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .header-content {
                flex-direction: column;
                gap: 1rem;
                text-align: center;
            }

            .nav-tabs {
                flex-direction: column;
            }

            .key-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }

            .key-actions {
                width: 100%;
                justify-content: flex-end;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>🔑 HackHub Key System</h1>
            <a href="/keysystem/logout" class="logout-btn">🚪 Logout</a>
        </div>
    </div>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_keys }}</div>
                <div class="stat-label">Total Keys</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ active_keys }}</div>
                <div class="stat-label">Active Keys</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ expired_keys }}</div>
                <div class="stat-label">Expired Keys</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_tasks }}</div>
                <div class="stat-label">Available Tasks</div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('keys')">🔑 Keys Management</button>
            <button class="nav-tab" onclick="showTab('tasks')">📋 Tasks</button>
            <button class="nav-tab" onclick="showTab('generate')">➕ Generate Key</button>
        </div>

        <!-- Keys Management Tab -->
        <div id="keys" class="tab-content active">
            <div class="card">
                <h2>🔑 Active Keys</h2>
                {% if user_keys %}
                    {% for user_id, key_data in user_keys.items() %}
                    <div class="key-item">
                        <div class="key-info">
                            <div class="key-code">{{ key_data.key }}</div>
                            <div class="key-meta">
                                <strong>User:</strong> {{ key_data.user_name }} (ID: {{ user_id }})<br>
                                <strong>Generated:</strong> {{ key_data.generated_at[:19] }}<br>
                                <strong>Expires:</strong> {{ key_data.expires_at[:19] }}<br>
                                <strong>Status:</strong> 
                                {% if key_data.is_active %}
                                    <span style="color: #48bb78;">Active</span>
                                {% else %}
                                    <span style="color: #e53e3e;">Expired</span>
                                {% endif %}
                            </div>
                        </div>
                        <div class="key-actions">
                            <button class="btn btn-sm btn-danger" onclick="revokeKey('{{ user_id }}')">Revoke</button>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="alert alert-error">No keys found in the system.</div>
                {% endif %}
            </div>
        </div>

        <!-- Tasks Tab -->
        <div id="tasks" class="tab-content">
            <div class="card">
                <h2>📋 Available Tasks</h2>
                <div class="task-item">
                    <div class="task-title">Join our Telegram Channel</div>
                    <div class="task-description">
                        Follow our official Telegram channel @hackhub_official to get latest updates and announcements.
                    </div>
                    <div class="task-reward">Reward: 24-hour Bot Access Key</div>
                    <button class="btn btn-sm">Complete Task</button>
                </div>
                
                <div class="task-item">
                    <div class="task-title">Share Bot with Friends</div>
                    <div class="task-description">
                        Share our giveaway bot with at least 3 friends and get them to use the bot.
                    </div>
                    <div class="task-reward">Reward: 48-hour Bot Access Key</div>
                    <button class="btn btn-sm">Complete Task</button>
                </div>
                
                <div class="task-item">
                    <div class="task-title">Leave a Review</div>
                    <div class="task-description">
                        Write a positive review about our bot and services on our social media platforms.
                    </div>
                    <div class="task-reward">Reward: 24-hour Bot Access Key</div>
                    <button class="btn btn-sm">Complete Task</button>
                </div>
                
                <div class="task-item">
                    <div class="task-title">Daily Check-in</div>
                    <div class="task-description">
                        Visit our website daily and complete the check-in process.
                    </div>
                    <div class="task-reward">Reward: 12-hour Bot Access Key</div>
                    <button class="btn btn-sm">Complete Task</button>
                </div>
            </div>
        </div>

        <!-- Generate Key Tab -->
        <div id="generate" class="tab-content">
            <div class="card">
                <h2>➕ Generate New Key</h2>
                <form method="POST" action="/keysystem/generate">
                    <div class="form-group">
                        <label for="user_name">User Name</label>
                        <input type="text" id="user_name" name="user_name" required placeholder="Enter user name">
                    </div>
                    <div class="form-group">
                        <label for="duration">Key Duration</label>
                        <select id="duration" name="duration" required>
                            <option value="12">12 Hours</option>
                            <option value="24" selected>24 Hours</option>
                            <option value="48">48 Hours</option>
                            <option value="72">72 Hours</option>
                            <option value="168">7 Days</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="note">Note (Optional)</label>
                        <textarea id="note" name="note" rows="3" placeholder="Add a note about this key..."></textarea>
                    </div>
                    <button type="submit" class="btn">Generate Key</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));

            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Show selected tab content
            document.getElementById(tabName).classList.add('active');

            // Add active class to clicked tab
            event.target.classList.add('active');
        }

        function revokeKey(userId) {
            if (confirm('Are you sure you want to revoke this key?')) {
                fetch('/keysystem/revoke', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({user_id: userId})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error revoking key: ' + data.error);
                    }
                });
            }
        }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HackHub Key System - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .login-container {
            background: white;
            padding: 3rem 2.5rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            width: 100%;
            max-width: 420px;
            backdrop-filter: blur(10px);
        }

        .logo {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .logo h1 {
            color: #2d3748;
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .logo p {
            color: #718096;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            color: #2d3748;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        input {
            width: 100%;
            padding: 0.875rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #f7fafc;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .login-btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.3);
        }

        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 0.875rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 0.875rem;
            border-left: 4px solid #c53030;
        }

        .success {
            background: #c6f6d5;
            color: #22543d;
            padding: 0.875rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 0.875rem;
            border-left: 4px solid #48bb78;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🔑 HackHub Key System</h1>
            <p>Admin Panel Access</p>
        </div>
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="login-btn">Login</button>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            {% if success %}
                <div class="success">{{ success }}</div>
            {% endif %}
        </form>
    </div>
</body>
</html>
"""

@app.route('/keysystem/')
def dashboard():
    if 'logged_in' not in session:
        return redirect('/keysystem/login')

    data = db.data
    user_keys = data.get('user_keys', {})
    
    # Calculate statistics
    total_keys = len(user_keys)
    active_keys = sum(1 for key_data in user_keys.values() if key_data.get('is_active', False))
    expired_keys = total_keys - active_keys
    total_tasks = 4  # Static number of available tasks

    return render_template_string(KEY_SYSTEM_TEMPLATE,
        user_keys=user_keys,
        total_keys=total_keys,
        active_keys=active_keys,
        expired_keys=expired_keys,
        total_tasks=total_tasks
    )

@app.route('/keysystem/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/keysystem/')
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/keysystem/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/keysystem/login')

@app.route('/keysystem/generate', methods=['POST'])
def generate_key():
    if 'logged_in' not in session:
        return redirect('/keysystem/login')

    user_name = request.form['user_name']
    duration_hours = int(request.form['duration'])
    note = request.form.get('note', '')

    # Generate random user ID for manual keys
    user_id = f"manual_{int(datetime.now().timestamp())}"
    
    # Generate random key
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    
    # Calculate expiry time
    expiry_time = datetime.now() + timedelta(hours=duration_hours)
    
    # Save to database
    if 'user_keys' not in db.data:
        db.data['user_keys'] = {}
        
    db.data['user_keys'][user_id] = {
        'key': key,
        'user_name': user_name,
        'generated_at': datetime.now().isoformat(),
        'expires_at': expiry_time.isoformat(),
        'is_active': True,
        'note': note,
        'manual_generated': True
    }
    
    db.save_data()
    
    return render_template_string(LOGIN_TEMPLATE, 
        success=f"Key generated successfully for {user_name}! Key: {key}")

@app.route('/keysystem/revoke', methods=['POST'])
def revoke_key():
    if 'logged_in' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    user_id = request.json.get('user_id')
    
    if user_id in db.data.get('user_keys', {}):
        db.data['user_keys'][user_id]['is_active'] = False
        db.save_data()
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Key not found"})

@app.route('/keysystem/api/keys')
def api_keys():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(db.data.get('user_keys', {}))

def start_key_system():
    try:
        print("🔑 Starting key system on port 3000...")
        app.run(host='0.0.0.0', port=3000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Key system error: {e}")
        time.sleep(5)
        # Retry on different port if 3000 is occupied
        try:
            print("🔑 Retrying key system on port 3001...")
            app.run(host='0.0.0.0', port=3001, debug=False, threaded=True, use_reloader=False)
        except Exception as e2:
            print(f"❌ Key system backup port error: {e2}")

if __name__ == '__main__':
    start_key_system()
