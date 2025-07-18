
from flask import Flask, render_template_string, request, jsonify
import subprocess
import psutil
import os
import signal
import time
from threading import Thread

app = Flask(__name__)

bot_process = None
bot_pid = None

def find_bot_process():
    """Find if the bot is already running"""
    global bot_pid
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                    bot_pid = proc.info['pid']
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error finding bot process: {e}")
    return False

def start_bot():
    """Start the bot process with enhanced error handling"""
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
    """Stop the bot process with enhanced error handling"""
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

def get_bot_status():
    """Get enhanced bot status with error handling"""
    try:
        if find_bot_process():
            try:
                proc = psutil.Process(bot_pid)
                return {
                    'running': True,
                    'pid': bot_pid,
                    'uptime': time.time() - proc.create_time(),
                    'memory': proc.memory_info().rss / 1024 / 1024,  # MB
                    'cpu': proc.cpu_percent()
                }
            except psutil.NoSuchProcess:
                return {'running': False}
        return {'running': False}
    except Exception as e:
        print(f"Error getting bot status: {e}")
        return {'running': False, 'error': str(e)}

BOT_CONTROL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 HackHub Bot Control Panel</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --glass-bg: rgba(255, 255, 255, 0.95);
            --glass-border: rgba(255, 255, 255, 0.3);
            --shadow-light: 0 25px 50px rgba(0, 0, 0, 0.15);
            --text-primary: #2d3748;
            --text-secondary: #718096;
            --success-color: #48bb78;
            --danger-color: #e53e3e;
            --warning-color: #ed8936;
        }

        [data-theme="dark"] {
            --glass-bg: rgba(30, 41, 59, 0.95);
            --glass-border: rgba(71, 85, 105, 0.3);
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --shadow-light: 0 25px 50px rgba(0, 0, 0, 0.6);
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
            transition: all 0.3s ease;
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

        .control-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            padding: 3rem;
            border-radius: 24px;
            box-shadow: var(--shadow-light);
            width: 100%;
            max-width: 600px;
            text-align: center;
            border: 1px solid var(--glass-border);
            position: relative;
            z-index: 1;
        }

        .header {
            margin-bottom: 2rem;
        }

        .header h1 {
            color: var(--text-primary);
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: var(--primary-gradient);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 500;
        }

        .theme-toggle {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255, 255, 255, 0.15);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: var(--text-primary);
            padding: 0.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.25rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .theme-toggle:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: scale(1.05);
        }

        .status-section {
            background: rgba(247, 250, 252, 0.8);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            border: 2px solid rgba(226, 232, 240, 0.5);
            transition: all 0.3s ease;
        }

        [data-theme="dark"] .status-section {
            background: rgba(30, 41, 59, 0.8);
            border-color: rgba(71, 85, 105, 0.5);
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-running .status-dot {
            background: var(--success-color);
        }

        .status-stopped .status-dot {
            background: var(--danger-color);
        }

        .status-running {
            color: var(--success-color);
        }

        .status-stopped {
            color: var(--danger-color);
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .stat-item {
            background: white;
            backdrop-filter: blur(10px);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(226, 232, 240, 0.5);
            transition: all 0.3s ease;
        }

        [data-theme="dark"] .stat-item {
            background: rgba(51, 65, 85, 0.8);
            border-color: rgba(71, 85, 105, 0.5);
        }

        .stat-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--primary-gradient);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        .control-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 16px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            min-width: 140px;
            justify-content: center;
            position: relative;
            overflow: hidden;
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

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-start {
            background: linear-gradient(135deg, var(--success-color), #38a169);
            color: white;
        }

        .btn-start:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(72, 187, 120, 0.3);
        }

        .btn-stop {
            background: linear-gradient(135deg, var(--danger-color), #c53030);
            color: white;
        }

        .btn-stop:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(229, 62, 62, 0.3);
        }

        .btn-refresh {
            background: var(--primary-gradient);
            color: white;
        }

        .btn-refresh:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .loading {
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

        .links-section {
            background: rgba(247, 250, 252, 0.8);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 20px;
            border: 2px solid rgba(226, 232, 240, 0.5);
        }

        [data-theme="dark"] .links-section {
            background: rgba(30, 41, 59, 0.8);
            border-color: rgba(71, 85, 105, 0.5);
        }

        .links-section h3 {
            color: var(--text-primary);
            margin-bottom: 1rem;
            font-size: 1.25rem;
        }

        .link-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            background: white;
            backdrop-filter: blur(10px);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border: 1px solid rgba(226, 232, 240, 0.5);
            transition: all 0.3s ease;
        }

        [data-theme="dark"] .link-item {
            background: rgba(51, 65, 85, 0.8);
            border-color: rgba(71, 85, 105, 0.5);
        }

        .link-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .link-item:last-child {
            margin-bottom: 0;
        }

        .link-label {
            font-weight: 500;
            color: var(--text-primary);
        }

        .link-url {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }

        .link-url:hover {
            text-decoration: underline;
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
            color: var(--success-color);
            border: 1px solid rgba(72, 187, 120, 0.3);
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger-color);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        /* Mobile Optimization */
        @media (max-width: 600px) {
            .control-panel {
                padding: 2rem;
                margin: 1rem;
            }

            .header h1 {
                font-size: 2rem;
            }

            .control-buttons {
                flex-direction: column;
            }

            .btn {
                width: 100%;
            }

            .stats-grid {
                grid-template-columns: 1fr 1fr;
            }

            .theme-toggle {
                position: static;
                margin-bottom: 1rem;
                align-self: flex-end;
            }
        }

        @media (max-width: 480px) {
            .control-panel {
                padding: 1.5rem;
            }

            .header h1 {
                font-size: 1.75rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark Mode">
        <span id="theme-icon">🌙</span>
    </button>

    <div class="control-panel">
        <div class="header">
            <h1>🤖 Bot Control</h1>
            <p>Enhanced HackHub Telegram Bot Manager</p>
        </div>

        <div id="alert-container"></div>

        <div class="status-section">
            <div id="status-indicator" class="status-indicator">
                <div class="status-dot"></div>
                <span id="status-text">Checking...</span>
            </div>
            <div id="bot-stats" class="stats-grid" style="display: none;">
                <div class="stat-item">
                    <div id="uptime-value" class="stat-value">-</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-item">
                    <div id="memory-value" class="stat-value">-</div>
                    <div class="stat-label">Memory</div>
                </div>
                <div class="stat-item">
                    <div id="cpu-value" class="stat-value">-</div>
                    <div class="stat-label">CPU</div>
                </div>
            </div>
        </div>

        <div class="control-buttons">
            <button id="start-btn" class="btn btn-start" onclick="startBot()">
                <span>▶️ Start Bot</span>
            </button>
            <button id="stop-btn" class="btn btn-stop" onclick="stopBot()">
                <span>⏹️ Stop Bot</span>
            </button>
            <button class="btn btn-refresh" onclick="refreshStatus()">
                <span>🔄 Refresh</span>
            </button>
        </div>

        <div class="links-section">
            <h3>🔗 Quick Links</h3>
            <div class="link-item">
                <span class="link-label">Dashboard</span>
                <a href="http://0.0.0.0:5000" class="link-url" target="_blank">Port 5000</a>
            </div>
            <div class="link-item">
                <span class="link-label">Key System</span>
                <a href="http://0.0.0.0:3000" class="link-url" target="_blank">Port 3000</a>
            </div>
            <div class="link-item">
                <span class="link-label">Keep Alive</span>
                <a href="http://0.0.0.0:8080" class="link-url" target="_blank">Port 8080</a>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;

        // Theme Management
        function initializeTheme() {
            const savedTheme = localStorage.getItem('bot-control-theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcon(savedTheme);
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('bot-control-theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            document.getElementById('theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
        }

        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
            
            alertContainer.innerHTML = `
                <div class="alert ${alertClass}">
                    ${message}
                </div>
            `;
            
            setTimeout(() => {
                alertContainer.innerHTML = '';
            }, 5000);
        }

        function updateStatus(data) {
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            const botStats = document.getElementById('bot-stats');
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');

            if (data.error) {
                statusIndicator.className = 'status-indicator status-stopped';
                statusText.textContent = `Error: ${data.error}`;
                botStats.style.display = 'none';
                startBtn.disabled = false;
                stopBtn.disabled = true;
                return;
            }

            if (data.running) {
                statusIndicator.className = 'status-indicator status-running';
                statusText.textContent = `Running (PID: ${data.pid})`;
                botStats.style.display = 'grid';
                
                const uptimeHours = Math.floor(data.uptime / 3600);
                const uptimeMinutes = Math.floor((data.uptime % 3600) / 60);
                document.getElementById('uptime-value').textContent = `${uptimeHours}h ${uptimeMinutes}m`;
                document.getElementById('memory-value').textContent = `${data.memory.toFixed(1)}MB`;
                document.getElementById('cpu-value').textContent = `${data.cpu.toFixed(1)}%`;
                
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                statusIndicator.className = 'status-indicator status-stopped';
                statusText.textContent = 'Stopped';
                botStats.style.display = 'none';
                
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }

        function setLoading(element, loading) {
            const span = element.querySelector('span');
            if (loading) {
                span.innerHTML = '<div class="loading"></div>';
                element.disabled = true;
            } else {
                if (element.id === 'start-btn') {
                    span.innerHTML = '▶️ Start Bot';
                } else if (element.id === 'stop-btn') {
                    span.innerHTML = '⏹️ Stop Bot';
                }
                element.disabled = false;
            }
        }

        async function startBot() {
            if (isLoading) return;
            
            isLoading = true;
            const startBtn = document.getElementById('start-btn');
            setLoading(startBtn, true);
            
            try {
                const response = await fetch('/start-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('✅ Bot started successfully!', 'success');
                    setTimeout(refreshStatus, 2000);
                } else {
                    showAlert(`❌ Failed to start bot: ${result.message}`, 'error');
                }
            } catch (error) {
                showAlert(`❌ Error starting bot: ${error.message}`, 'error');
            } finally {
                setLoading(startBtn, false);
                isLoading = false;
            }
        }

        async function stopBot() {
            if (isLoading) return;
            
            isLoading = true;
            const stopBtn = document.getElementById('stop-btn');
            setLoading(stopBtn, true);
            
            try {
                const response = await fetch('/stop-bot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('✅ Bot stopped successfully!', 'success');
                    setTimeout(refreshStatus, 2000);
                } else {
                    showAlert(`❌ Failed to stop bot: ${result.message}`, 'error');
                }
            } catch (error) {
                showAlert(`❌ Error stopping bot: ${error.message}`, 'error');
            } finally {
                setLoading(stopBtn, false);
                isLoading = false;
            }
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/bot-status');
                const data = await response.json();
                updateStatus(data);
            } catch (error) {
                console.error('Error fetching status:', error);
                showAlert('❌ Error fetching bot status', 'error');
            }
        }

        // Error handling
        window.addEventListener('error', function(e) {
            console.error('Control Panel Error:', e.error);
            showAlert('❌ An error occurred. Please refresh the page.', 'error');
        });

        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            initializeTheme();
            refreshStatus();
            setInterval(refreshStatus, 5000);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(BOT_CONTROL_TEMPLATE)

@app.route('/bot-status')
def bot_status():
    try:
        return jsonify(get_bot_status())
    except Exception as e:
        return jsonify({"error": str(e), "running": False}), 500

@app.route('/start-bot', methods=['POST'])
def start_bot_endpoint():
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
    try:
        if not get_bot_status()['running']:
            return jsonify({'success': False, 'message': 'Bot is not running'})
        
        if stop_bot():
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to stop bot'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def start_web_control():
    try:
        print("🎮 Starting enhanced bot control web interface on port 7000...")
        app.run(host='0.0.0.0', port=7000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Bot control web interface error: {e}")
        time.sleep(5)
        try:
            print("🎮 Retrying enhanced bot control web interface on port 7001...")
            app.run(host='0.0.0.0', port=7001, debug=False, threaded=True, use_reloader=False)
        except Exception as e2:
            print(f"❌ Bot control web interface backup port error: {e2}")

if __name__ == '__main__':
    start_web_control()
