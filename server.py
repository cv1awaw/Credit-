# server.py
import os
import threading
import asyncio
from flask import Flask

def start_bot():
    # Create an event loop for this thread so PTB can run polling
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    import main as bot
    # Your main() builds Application and calls run_polling()
    bot.main()

threading.Thread(target=start_bot, daemon=True).start()

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Koyeb health check uses port 8000 by default
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
