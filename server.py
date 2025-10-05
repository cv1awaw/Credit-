# server.py
import os, threading
from flask import Flask

def start_bot():
    import main            # if your bot doesn’t auto-start on import, expose main.run() and call it here
    # main.run()  # <- uncomment and use if you have a run() function

threading.Thread(target=start_bot, daemon=True).start()

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
