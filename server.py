# server.py
import os, threading
from flask import Flask

def start_bot():
    # Import your script and explicitly call main()
    import main as bot
    bot.main()  # <-- your script has a main() that starts Application.run_polling()

# run the bot in a background thread so the web server can answer health checks
threading.Thread(target=start_bot, daemon=True).start()

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Koyeb's default health-check port is 8000
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
