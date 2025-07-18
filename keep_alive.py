from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 5000))  # 💡 Guna port dari Render
    print(f"💓 Starting keep_alive on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.start()
