# server.py
import os
import threading
from flask import Flask

# --- tiny HTTP server for Koyeb health checks ---
app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # 1) Start Flask in a background thread (for health checks)
    threading.Thread(target=run_flask, daemon=True).start()

    # 2) Run your Telegram bot in the MAIN thread (so PTB can set signal handlers)
    import main as bot
    # your main() builds Application and calls run_polling()
    bot.main()
