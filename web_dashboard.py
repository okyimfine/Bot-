"""
Enhanced HackHub Bot Dashboard with Dark Mode, Mobile Optimization, and New Features
"""
from flask import Flask, render_template_string, request, redirect, session, jsonify
from database import db
import json
import time
import hashlib
import base64
import psutil
import subprocess
import os
import signal
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'hackhub_secret_key_2025_enhanced'

# Admin credentials
ADMIN_USERNAME = "man"
ADMIN_PASSWORD = "23148"

# Store bot process info
bot_process = None
bot_pid = None

def find_bot_process():
    """Find if the bot is already running"""
    global bot_pid
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                bot_pid = proc.info['pid']
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def start_bot():
    """Start the bot process"""
    global bot_process, bot_pid
    try:
        bot_process = subprocess.Popen(['python', 'main.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     preexec_fn=os.setsid)
        bot_pid = bot_process.pid
        return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        return False

def stop_bot():
    """Stop the bot process"""
    global bot_process, bot_pid
    try:
        if bot_pid:
            try:
                proc = psutil.Process(bot_pid)
                proc.terminate()
                proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(bot_pid), signal.SIGTERM)
                except:
                    pass

            bot_process = None
            bot_pid = None
            return True
    except Exception as e:
        print(f"Error stopping bot: {e}")
        return False

def get_system_metrics():
    """Get comprehensive system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used / 1024 / 1024 / 1024,  # GB
            'memory_total': memory.total / 1024 / 1024 / 1024,  # GB
            'disk_percent': disk.percent,
            'disk_used': disk.used / 1024 / 1024 / 1024,  # GB
            'disk_total': disk.total / 1024 / 1024 / 1024,  # GB
            'network_sent': network.bytes_sent / 1024 / 1024,  # MB
            'network_recv': network.bytes_recv / 1024 / 1024,  # MB
        }
    except Exception as e:
        print(f"Error getting system metrics: {e}")
        return {}

def get_bot_status():
    """Get enhanced bot status information"""
    bot_running = find_bot_process()
    system_metrics = get_system_metrics()

    if bot_running and bot_pid:
        try:
            proc = psutil.Process(bot_pid)
            process_memory = proc.memory_info()
            process_uptime = datetime.now() - datetime.fromtimestamp(proc.create_time())

            hours = int(process_uptime.total_seconds() // 3600)
            minutes = int((process_uptime.total_seconds() % 3600) // 60)

            return {
                'status': 'Online',
                'uptime': f'{hours}h {minutes}m',
                'last_restart': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                'memory_usage': f'{process_memory.rss / 1024 / 1024:.1f} MB',
                'cpu_usage': f'{proc.cpu_percent():.1f}%',
                'active_connections': len(db.data.get('active_giveaways', {})),
                'messages_processed': sum(stats.get('total_participations', 0) for stats in db.data.get('user_stats', {}).values()),
                'errors_count': 0,
                'running': True,
                'pid': bot_pid,
                'bot_uptime': process_uptime.total_seconds(),
                'bot_memory': process_memory.rss / 1024 / 1024,
                'bot_cpu': proc.cpu_percent(),
                'system_metrics': system_metrics
            }
        except psutil.NoSuchProcess:
            bot_running = False

    return {
        'status': 'Offline',
        'uptime': '0h 0m',
        'last_restart': 'Never',
        'memory_usage': '0 MB',
        'cpu_usage': '0%',
        'active_connections': 0,
        'messages_processed': 0,
        'errors_count': 0,
        'running': False,
        'system_metrics': system_metrics
    }

def get_analytics_data():
    """Get enhanced analytics data"""
    data = db.data
    now = datetime.now()

    # Calculate time-based statistics
    daily_stats = {'participations': 0, 'completions': 0, 'new_users': 0}
    weekly_stats = {'participations': 0, 'completions': 0, 'new_users': 0}
    monthly_stats = {'participations': 0, 'completions': 0, 'new_users': 0}

    # Top participants
    user_participation_counts = {}
    for user_id, stats in data.get('user_stats', {}).items():
        user_participation_counts[stats.get('name', f'User {user_id}')] = stats.get('total_participations', 0)

    top_participants = sorted(user_participation_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Recent activity
    recent_giveaways = data.get('completed_giveaways', [])[-10:]

    # Win rate analysis
    total_giveaways = len(data.get('completed_giveaways', []))
    total_participants = sum(stats.get('total_participations', 0) for stats in data.get('user_stats', {}).values())
    avg_participation = total_participants / total_giveaways if total_giveaways > 0 else 0

    return {
        'daily_stats': daily_stats,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'top_participants': top_participants,
        'recent_giveaways': recent_giveaways,
        'total_giveaways': total_giveaways,
        'avg_participation': avg_participation,
        'user_growth': len(data.get('user_stats', {}))
    }

def get_player_status():
    """Get enhanced player status and activity"""
    data = db.data
    players = []

    for user_id, stats in data.get('user_stats', {}).items():
        last_activity_str = stats.get('last_activity', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        try:
            last_activity_time = datetime.strptime(last_activity_str[:19], '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - last_activity_time

            if time_diff.total_seconds() < 300:  # 5 minutes
                activity_status = "Active"
                status_color = "success"
            elif time_diff.total_seconds() < 3600:  # 1 hour
                activity_status = "Inactive"
                status_color = "warning"
            else:
                activity_status = "Offline"
                status_color = "danger"

            if time_diff.total_seconds() < 60:
                time_ago = f"{int(time_diff.total_seconds())} seconds ago"
            elif time_diff.total_seconds() < 3600:
                time_ago = f"{int(time_diff.total_seconds() // 60)} minutes ago"
            elif time_diff.total_seconds() < 86400:
                time_ago = f"{int(time_diff.total_seconds() // 3600)} hours ago"
            else:
                time_ago = f"{int(time_diff.total_seconds() // 86400)} days ago"
        except:
            activity_status = "Unknown"
            status_color = "danger"
            last_activity_str = "Never"
            time_ago = "Never"

        join_date = stats.get('first_join', '2025-01-01')
        total_participations = stats.get('total_participations', 0)
        total_wins = stats.get('total_wins', 0)
        win_rate = (total_wins / total_participations * 100) if total_participations > 0 else 0

        has_active_key = db.validate_user_key(int(user_id))
        key_status = "Valid" if has_active_key else "Expired/None"

        players.append({
            'user_id': user_id,
            'name': stats.get('name', 'Unknown'),
            'status': activity_status,
            'status_color': status_color,
            'last_activity': last_activity_str,
            'time_ago': time_ago,
            'total_participations': total_participations,
            'total_wins': total_wins,
            'win_rate': win_rate,
            'join_date': join_date,
            'key_status': key_status,
            'has_active_key': has_active_key
        })

    players.sort(key=lambda x: x['last_activity'], reverse=True)
    return players

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HackHub Bot Dashboard - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --glass-bg: rgba(255, 255, 255, 0.95);
            --glass-border: rgba(255, 255, 255, 0.3);
            --shadow-light: 0 25px 50px rgba(0, 0, 0, 0.15);
            --text-primary: #2d3748;
            --text-secondary: #718096;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        body::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            animation: float 20s infinite ease-in-out;
            pointer-events: none;
        }

        @keyframes float {
            0%, 100% { transform: translate(-25%, -25%) rotate(0deg); }
            50% { transform: translate(-30%, -30%) rotate(180deg); }
        }

        .login-container {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            padding: 3rem 2.5rem;
            border-radius: 24px;
            box-shadow: var(--shadow-light);
            width: 100%;
            max-width: 420px;
            border: 1px solid var(--glass-border);
            position: relative;
            z-index: 1;
        }

        .logo {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .logo h1 {
            color: var(--text-primary);
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: var(--primary-gradient);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo p {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: rgba(247, 250, 252, 0.8);
            backdrop-filter: blur(10px);
        }

        input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }

        .login-btn {
            width: 100%;
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 1.125rem;
            border-radius: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .login-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.6s ease;
        }

        .login-btn:hover::before {
            left: 100%;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        }

        .error {
            background: linear-gradient(135deg, #fed7d7, #feb2b2);
            color: #c53030;
            padding: 1rem;
            border-radius: 12px;
            margin-top: 1rem;
            font-size: 0.875rem;
            border-left: 4px solid #e53e3e;
            backdrop-filter: blur(10px);
        }

        @media (max-width: 480px) {
            .login-container {
                padding: 2rem 1.5rem;
                margin: 1rem;
            }

            .logo h1 {
                font-size: 1.75rem;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🚀 HackHub Bot</h1>
            <p>Enhanced Dashboard Login</p>
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
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HackHub Bot Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            /* Light theme colors */
            --bg-primary: #f8fafc;
            --bg-secondary: rgba(255, 255, 255, 0.95);
            --bg-tertiary: #f1f5f9;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-muted: #718096;
            --border-color: rgba(226, 232, 240, 0.6);
            --accent-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-success: #48bb78;
            --accent-warning: #ed8936;
            --accent-danger: #e53e3e;
            --shadow-light: 0 4px 6px rgba(0, 0, 0, 0.05);
            --shadow-medium: 0 10px 25px rgba(0, 0, 0, 0.1);
            --shadow-heavy: 0 25px 50px rgba(0, 0, 0, 0.15);
            --glass-bg: rgba(255, 255, 255, 0.95);
            --glass-border: rgba(255, 255, 255, 0.3);
        }

        [data-theme="dark"] {
            /* Dark theme colors */
            --bg-primary: #0f172a;
            --bg-secondary: rgba(30, 41, 59, 0.95);
            --bg-tertiary: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: rgba(71, 85, 105, 0.6);
            --accent-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            --shadow-light: 0 4px 6px rgba(0, 0, 0, 0.3);
            --shadow-medium: 0 10px 25px rgba(0, 0, 0, 0.4);
            --shadow-heavy: 0 25px 50px rgba(0, 0, 0, 0.6);
            --glass-bg: rgba(30, 41, 59, 0.95);
            --glass-border: rgba(71, 85, 105, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            transition: all 0.3s ease;
        }

        .header {
            background: var(--accent-primary);
            color: white;
            padding: 2rem 0;
            box-shadow: var(--shadow-heavy);
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            pointer-events: none;
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 1;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .header p {
            opacity: 0.9;
            font-size: 0.875rem;
        }

        .header-actions {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .theme-toggle {
            background: rgba(255, 255, 255, 0.15);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 0.75rem;
            border-radius: 12px;
            cursor: pointer;
            font-size: 1.25rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .theme-toggle:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: scale(1.05);
        }

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            position: relative;
            overflow: hidden;
            font-size: 0.875rem;
            backdrop-filter: blur(10px);
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.6s ease;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn-primary {
            background: rgba(255, 255, 255, 0.15);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .btn-primary:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }

        .btn-danger {
            background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
            color: white;
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(229, 62, 62, 0.3);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        .nav-tabs {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            box-shadow: var(--shadow-medium);
            display: flex;
            overflow-x: auto;
            border-radius: 0 0 20px 20px;
            border: 1px solid var(--border-color);
            border-top: none;
        }

        .nav-tab {
            padding: 1.5rem 2.5rem;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-muted);
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            white-space: nowrap;
            position: relative;
            overflow: hidden;
        }

        .nav-tab::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
            transition: left 0.6s ease;
        }

        .nav-tab:hover::before {
            left: 100%;
        }

        .nav-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        }

        .nav-tab:hover {
            color: #667eea;
            background: var(--bg-tertiary);
        }

        .main-content {
            padding: 2rem 0;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--glass-bg);
            backdrop-filter: blur(15px);
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.6s ease;
        }

        .stat-card:hover::before {
            left: 100%;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-heavy);
        }

        .stat-number {
            font-size: 3rem;
            font-weight: 800;
            background: var(--accent-primary);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.75rem;
        }

        .stat-label {
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.5px;
        }

        .section {
            background: var(--glass-bg);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }

        .section:hover {
            box-shadow: var(--shadow-heavy);
        }

        .section h2 {
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 2rem;
            position: relative;
            padding-bottom: 1rem;
        }

        .section h2::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 60px;
            height: 3px;
            background: var(--accent-primary);
            border-radius: 2px;
        }

        .giveaway-card {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .giveaway-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
```python
            background: var(--accent-primary);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .giveaway-card:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-medium);
        }

        .giveaway-card:hover::before {
            opacity: 1;
        }

        .giveaway-card.active {
            border-left: 6px solid var(--accent-success);
            background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, rgba(72, 187, 120, 0.05) 100%);
        }

        .mobile-responsive {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }

        .chart-container {
            background: var(--glass-bg);
            backdrop-filter: blur(15px);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-color);
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-primary);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .alert {
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            font-weight: 500;
            backdrop-filter: blur(10px);
        }

        .alert-success {
            background: rgba(72, 187, 120, 0.1);
            color: var(--accent-success);
            border: 1px solid rgba(72, 187, 120, 0.3);
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            color: var(--accent-danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: var(--shadow-heavy);
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease forwards;
        }

        /* Mobile Optimization */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 1.5rem;
                text-align: center;
                padding: 0 1rem;
            }

            .header h1 {
                font-size: 2rem;
            }

            .header-actions {
                flex-wrap: wrap;
                justify-content: center;
                gap: 0.75rem;
            }

            .container {
                padding: 0 1rem;
            }

            .section {
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }

            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }

            .stat-card {
                padding: 1.5rem;
            }

            .stat-number {
                font-size: 2.25rem;
            }

            .nav-tab {
                padding: 1rem 1.5rem;
                font-size: 0.875rem;
            }

            .btn {
                padding: 0.875rem 1.5rem;
                font-size: 0.8rem;
            }

            .mobile-responsive {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.75rem;
            }

            .section h2 {
                font-size: 1.25rem;
            }

            .stat-number {
                font-size: 2rem;
            }

            .stat-card {
                padding: 1.25rem;
            }

            .nav-tabs {
                overflow-x: auto;
                scrollbar-width: none;
                -ms-overflow-style: none;
            }

            .nav-tabs::-webkit-scrollbar {
                display: none;
            }
        }

        /* Dark mode specific adjustments */
        [data-theme="dark"] .nav-tab:hover {
            background: rgba(71, 85, 105, 0.3);
        }

        [data-theme="dark"] .stat-card:hover {
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6);
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--accent-primary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div>
                <h1>🚀 HackHub Bot Dashboard</h1>
                <p>Last updated: {{ last_updated }}</p>
            </div>
            <div class="header-actions">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark Mode">
                    <span id="theme-icon">🌙</span>
                </button>
                <a href="javascript:refreshData()" class="btn btn-primary">
                    🔄 Refresh
                </a>
                <a href="/logout" class="btn btn-danger">
                    🚪 Logout
                </a>
            </div>
        </div>
    </div>

    <div class="nav-tabs">
        <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
        <button class="nav-tab" onclick="showTab('analytics')">📈 Analytics</button>
        <button class="nav-tab" onclick="showTab('bot-control')">🎮 Bot Control</button>
        <button class="nav-tab" onclick="showTab('players')">👥 Players</button>
        <button class="nav-tab" onclick="showTab('system')">⚙️ System</button>
    </div>

    <div class="container">
        <div class="main-content">
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card fade-in-up">
                        <div class="stat-number">{{ active_count }}</div>
                        <div class="stat-label">Active Giveaways</div>
                    </div>
                    <div class="stat-card fade-in-up">
                        <div class="stat-number">{{ total_completed }}</div>
                        <div class="stat-label">Completed Giveaways</div>
                    </div>
                    <div class="stat-card fade-in-up">
                        <div class="stat-number">{{ total_users }}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    <div class="stat-card fade-in-up">
                        <div class="stat-number">{{ total_participations }}</div>
                        <div class="stat-label">Total Participations</div>
                    </div>
                </div>

                <div class="section">
                    <h2>🎉 Active Giveaways</h2>
                    {% if active_giveaways %}
                        {% for msg_id, giveaway in active_giveaways.items() %}
                        <div class="giveaway-card active">
                            <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem;">{{ giveaway.title }}</div>
                            <div class="mobile-responsive">
                                <div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">GIFT</div>
                                    <div style="font-weight: 500;">{{ giveaway.gift }}</div>
                                </div>
                                <div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">DURATION</div>
                                    <div style="font-weight: 500;">
                                        {% if giveaway.end_time %}
                                            <span class="countdown-timer" data-end-time="{{ giveaway.end_time }}">Calculating...</span>
                                        {% else %}
                                            ♾️ Unlimited
                                        {% endif %}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">PARTICIPANTS</div>
                                    <div style="font-weight: 500;">{{ participants.get(msg_id, [])|length }} people</div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                            <h3>No Active Giveaways</h3>
                            <p>There are currently no active giveaways running.</p>
                        </div>
                    {% endif %}
                </div>
            </div>

            <!-- Analytics Tab -->
            <div id="analytics" class="tab-content">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{{ analytics.total_giveaways }}</div>
                        <div class="stat-label">Total Giveaways</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ "%.1f"|format(analytics.avg_participation) }}</div>
                        <div class="stat-label">Avg Participation</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ analytics.user_growth }}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                </div>

                <div class="section">
                    <h2>📈 Top Participants</h2>
                    <div class="mobile-responsive">
                        {% for name, count in analytics.top_participants %}
                        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 12px; margin-bottom: 0.5rem;">
                            <div style="font-weight: 600;">{{ name }}</div>
                            <div style="color: var(--text-muted); font-size: 0.875rem;">{{ count }} participations</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="section">
                    <h2>🏆 Recent Giveaways</h2>
                    {% for giveaway in analytics.recent_giveaways %}
                    <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                        <div style="font-weight: 500;">{{ giveaway.title }}</div>
                        <div style="color: var(--text-muted); font-size: 0.875rem;">{{ giveaway.participants|length }} participants</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Bot Control Tab -->
            <div id="bot-control" class="tab-content">
                <div class="section">
                    <h2>🎮 Bot Control Panel</h2>

                    <div id="alert-container" style="margin-bottom: 1rem;"></div>

                    <div class="stats-grid" style="margin-bottom: 2rem;">
                        <div class="stat-card">
                            <div id="bot-status-indicator" class="stat-number" style="color: var(--accent-danger);">Checking...</div>
                            <div class="stat-label">Bot Status</div>
                        </div>
                        <div class="stat-card">
                            <div id="bot-uptime" class="stat-number">-</div>
                            <div class="stat-label">Bot Uptime</div>
                        </div>
                        <div class="stat-card">
                            <div id="bot-memory" class="stat-number">-</div>
                            <div class="stat-label">Bot Memory</div>
                        </div>
                        <div class="stat-card">
                            <div id="bot-cpu" class="stat-number">-</div>
                            <div class="stat-label">Bot CPU</div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 1rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap;">
                        <button id="start-bot-btn" class="btn" onclick="startBotControl()" style="background: linear-gradient(135deg, #48bb78, #38a169); color: white;">
                            ▶️ Start Bot
                        </button>
                        <button id="stop-bot-btn" class="btn" onclick="stopBotControl()" style="background: linear-gradient(135deg, #e53e3e, #c53030); color: white;">
                            ⏹️ Stop Bot
                        </button>
                        <button class="btn" onclick="refreshBotStatus()" style="background: var(--accent-primary); color: white;">
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            </div>

            <!-- Players Tab -->
            <div id="players" class="tab-content">
                <div class="section">
                    <h2>👥 Player Management</h2>
                    <div class="mobile-responsive">
                        {% for player in player_status %}
                        <div class="giveaway-card" style="margin-bottom: 1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                                <div>
                                    <div style="font-weight: 600; font-size: 1.125rem;">{{ player.name }}</div>
                                    <div style="color: var(--text-muted); font-size: 0.875rem;">ID: {{ player.user_id }}</div>
                                </div>
                                <div style="text-align: right;">
                                    <span style="padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; 
                                    {% if player.status == 'Active' %}background: rgba(72, 187, 120, 0.1); color: var(--accent-success);
                                    {% elif player.status == 'Inactive' %}background: rgba(237, 137, 54, 0.1); color: var(--accent-warning);
                                    {% else %}background: rgba(239, 68, 68, 0.1); color: var(--accent-danger);{% endif %}">
                                        ● {{ player.status }}
                                    </span>
                                </div>
                            </div>

                            <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span style="color: var(--text-muted);">Last Seen</span>
                                    <span style="font-weight: 500;">{{ player.time_ago }}</span>
                                </div>
                            </div>

                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 1rem;">
                                <div style="text-align: center;">
                                    <div style="font-weight: 700; font-size: 1.25rem; color: #667eea;">{{ player.total_participations }}</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted);">PARTICIPATIONS</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-weight: 700; font-size: 1.25rem; color: #667eea;">{{ player.total_wins }}</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted);">WINS</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-weight: 700; font-size: 1.25rem; color: #667eea;">{{ "%.1f"|format(player.win_rate) }}%</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted);">WIN RATE</div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- System Tab -->
            <div id="system" class="tab-content">
                <div class="section">
                    <h2>⚙️ System Metrics</h2>

                    {% if bot_status.system_metrics %}
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ "%.1f"|format(bot_status.system_metrics.cpu_percent) }}%</div>
                            <div class="stat-label">CPU Usage</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {{ bot_status.system_metrics.cpu_percent }}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ "%.1f"|format(bot_status.system_metrics.memory_percent) }}%</div>
                            <div class="stat-label">Memory Usage</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {{ bot_status.system_metrics.memory_percent }}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ "%.1f"|format(bot_status.system_metrics.disk_percent) }}%</div>
                            <div class="stat-label">Disk Usage</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {{ bot_status.system_metrics.disk_percent }}%"></div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    <div class="chart-container">
                        <h3 style="margin-bottom: 1rem;">📊 Performance Overview</h3>
                        <div style="display: grid; gap: 1rem;">
                            <div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span>Active Connections</span>
                                    <span style="font-weight: 600;">{{ bot_status.active_connections }}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span>Messages Processed</span>
                                    <span style="font-weight: 600;">{{ bot_status.messages_processed }}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <span>Error Count</span>
                                    <span style="font-weight: 600; color: var(--accent-success);">{{ bot_status.errors_count }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Theme Management
        function initializeTheme() {
            const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcon(savedTheme);
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('dashboard-theme', newTheme);
            updateThemeIcon(newTheme);

            showNotification(newTheme === 'dark' ? '🌙 Dark mode enabled' : '☀️ Light mode enabled');
        }

        function updateThemeIcon(theme) {
            document.getElementById('theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
        }

        // Notification System
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.25rem;">×</button>
                </div>
            `;

            document.body.appendChild(notification);

            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Tab Management
        function showTab(tabName) {
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));

            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => tab.classList.remove('active'));

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            localStorage.setItem('active-tab', tabName);
        }

        function restoreActiveTab() {
            const savedTab = localStorage.getItem('active-tab') || 'overview';
            const tabButton = document.querySelector(`[onclick="showTab('${savedTab}')"]`);
            if (tabButton) {
                showTab(savedTab);
                tabButton.classList.add('active');
            }
        }

        // Bot Control Functions with enhanced error handling
        async function startBotControl() {
            const startBtn = document.getElementById('start-bot-btn');
            if (!startBtn) return;

            try {
                startBtn.disabled = true;
                startBtn.innerHTML = '⏳ Starting...';

                showAlert('Starting bot...', 'info');
                const response = await fetch('/start-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();

                if (result.success) {
                    showAlert('✅ Bot started successfully!', 'success');
                    showNotification('🤖 Bot started successfully!');
                    setTimeout(refreshBotStatus, 2000);
                } else {
                    showAlert(`❌ Failed to start bot: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error('Start bot error:', error);
                showAlert(`❌ Error starting bot: ${error.message}`, 'error');
            } finally {
                startBtn.disabled = false;
                startBtn.innerHTML = '▶️ Start Bot';
            }
        }

        async function stopBotControl() {
            const stopBtn = document.getElementById('stop-bot-btn');
            if (!stopBtn) return;

            try {
                stopBtn.disabled = true;
                stopBtn.innerHTML = '⏳ Stopping...';

                showAlert('Stopping bot...', 'info');
                const response = await fetch('/stop-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();

                if (result.success) {
                    showAlert('✅ Bot stopped successfully!', 'success');
                    showNotification('🛑 Bot stopped successfully!');
                    setTimeout(refreshBotStatus, 2000);
                } else {
                    showAlert(`❌ Failed to stop bot: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error('Stop bot error:', error);
                showAlert(`❌ Error stopping bot: ${error.message}`, 'error');
            } finally {
                stopBtn.disabled = false;
                stopBtn.innerHTML = '⏹️ Stop Bot';
            }
        }

        async function refreshBotStatus() {
            try {
                const response = await fetch('/bot-control-status');

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                const statusIndicator = document.getElementById('bot-status-indicator');
                const uptimeElement = document.getElementById('bot-uptime');
                const memoryElement = document.getElementById('bot-memory');
                const cpuElement = document.getElementById('bot-cpu');

                if (!statusIndicator || !uptimeElement || !memoryElement || !cpuElement) {
                    console.warn('Bot status elements not found');
                    return;
                }

                if (data.error) {
                    statusIndicator.textContent = `⚠️ Error: ${data.error}`;
                    statusIndicator.style.color = 'var(--accent-warning)';

                    uptimeElement.textContent = '-';
                    memoryElement.textContent = '-';
                    cpuElement.textContent = '-';
                } else if (data.running) {
                    statusIndicator.textContent = '✅ Running';
                    statusIndicator.style.color = 'var(--accent-success)';

                    const uptimeHours = Math.floor((data.uptime || 0) / 3600);
                    const uptimeMinutes = Math.floor(((data.uptime || 0) % 3600) / 60);
                    uptimeElement.textContent = `${uptimeHours}h ${uptimeMinutes}m`;
                    memoryElement.textContent = `${(data.memory || 0).toFixed(1)}MB`;
                    cpuElement.textContent = `${(data.cpu || 0).toFixed(1)}%`;
                } else {
                    statusIndicator.textContent = '❌ Stopped';
                    statusIndicator.style.color = 'var(--accent-danger)';

                    uptimeElement.textContent = '-';
                    memoryElement.textContent = '-';
                    cpuElement.textContent = '-';
                }
            } catch (error) {
                console.error('Error fetching bot status:', error);
                const statusIndicator = document.getElementById('bot-status-indicator');
                if (statusIndicator) {
                    statusIndicator.textContent = '⚠️ Connection Error';
                    statusIndicator.style.color = 'var(--accent-warning)';
                }
            }
        }

        function updateCountdowns() {
            const countdownElements = document.querySelectorAll('.countdown-timer');
            countdownElements.forEach(element => {
                const endTime = parseInt(element.dataset.endTime);
                if (endTime && endTime > 0) {
                    const now = Math.floor(Date.now() / 1000);
                    const remaining = Math.max(0, endTime - now);

                    if (remaining > 0) {
                        const hours = Math.floor(remaining / 3600);
                        const minutes = Math.floor((remaining % 3600) / 60);
                        const seconds = remaining % 60;

                        let timeString = '';
                        if (hours > 0) {
                            timeString = `${hours}h ${minutes}m ${seconds}s`;
                        } else if (minutes > 0) {
                            timeString = `${minutes}m ${seconds}s`;
                        } else {
                            timeString = `${seconds}s`;
                        }

                        element.textContent = timeString;
                        element.style.color = remaining < 60 ? 'var(--accent-danger)' : 'var(--accent-success)';
                    } else {
                        element.textContent = 'ENDED';
                        element.style.color = 'var(--accent-danger)';
                    }
                }
            });
        }

        function refreshData() {
            showNotification('🔄 Refreshing data...');
            location.reload();
        }

        // Enhanced error handling
        window.addEventListener('error', function(e) {
            console.error('Dashboard Error:', e.error);
            if (e.error && e.error.message) {
                showAlert(`❌ Error: ${e.error.message}`, 'error');
            } else {
                showAlert('❌ An error occurred. Please refresh the page.', 'error');
            }
        });

        window.addEventListener('unhandledrejection', function(e) {
            console.error('Unhandled Promise Rejection:', e.reason);
            showAlert('❌ Network error occurred. Please try again.', 'error');
        });

        // Initialize on load with error handling
        document.addEventListener('DOMContentLoaded', function() {
            try {
                initializeTheme();
                restoreActiveTab();
                refreshBotStatus();
                updateCountdowns();

                // Auto-refresh
                setInterval(refreshBotStatus, 5000);
                setInterval(updateCountdowns, 1000);

                // Add fade-in animation
                document.querySelectorAll('.stat-card').forEach((card, index) => {
                    card.style.animationDelay = `${index * 0.1}s`;
                });

            } catch (error) {
                console.error('Dashboard initialization error:', error);
                showAlert('❌ Failed to initialize dashboard', 'error');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    if 'logged_in' not in session:
        return redirect('/login')

    try:
        data = db.data
        bot_status = get_bot_status()
        player_status = get_player_status()
        analytics = get_analytics_data()

        return render_template_string(DASHBOARD_TEMPLATE,
            last_updated=data.get('last_updated', 'Never'),
            active_count=len(data.get('active_giveaways', {})),
            total_completed=len(data.get('completed_giveaways', [])),
            total_users=len(data.get('user_stats', {})),
            total_participations=sum(stats.get('total_participations', 0) for stats in data.get('user_stats', {}).values()),
            active_giveaways=data.get('active_giveaways', {}),
            participants=data.get('participants', {}),
            user_stats=data.get('user_stats', {}),
            completed_giveaways=data.get('completed_giveaways', []),
            bot_status=bot_status,
            player_status=player_status,
            analytics=analytics
        )
    except Exception as e:
        print(f"Dashboard error: {e}")
        return f"Dashboard Error: {e}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/api/data')
def api_data():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(db.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot-status')
def api_bot_status():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(get_bot_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics')
def api_analytics():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(get_analytics_data())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/bot-control-status')
def bot_control_status():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(get_bot_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start-bot', methods=['POST'])
def start_bot_endpoint():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        if get_bot_status()['running']:
            return jsonify({'success': False, 'message': 'Bot is already running'})

        if start_bot():
            return jsonify({'success': True, 'message': 'Bot started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start bot'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/stop-bot', methods=['POST'])
def stop_bot_endpoint():
    if 'logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        if not get_bot_status()['running']:
            return jsonify({'success': False, 'message': 'Bot is not running'})

        if stop_bot():
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to stop bot'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def start_web_dashboard():
    try:
        print("🌐 Starting enhanced web dashboard on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Web dashboard error: {e}")
        time.sleep(5)
        try:
            print("🌐 Retrying enhanced web dashboard on port 5001...")
            app.run(host='0.0.0.0', port=5001, debug=False, threaded=True, use_reloader=False)
        except Exception as e2:
            print(f"❌ Web dashboard backup port error: {e2}")

if __name__ == '__main__':
    start_web_dashboard()