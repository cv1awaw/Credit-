# server.py
import os, threading
from flask import Flask

def start_bot():
    import main  # this starts your Telegram bot
    # If your bot doesn't auto-start on import, expose a function like main.run() and call it here.

threading.Thread(target=start_bot, daemon=True).start()

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
