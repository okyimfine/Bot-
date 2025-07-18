from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    print("💓 Starting keep_alive on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.start()