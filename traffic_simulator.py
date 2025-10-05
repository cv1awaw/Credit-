# traffic_simulator.py
import asyncio
import random
import time
import logging
from datetime import datetime
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================== CONFIG ==================
# غيّر BASE_URL إلى رابط موقعك (يجب أن يبدأ بـ http:// أو https://)
BASE_URL = "https://your-site.example"

# قائمة المسارات التي تريد أن يزورهم السكربت
ENDPOINTS = [
    "/",                # الصفحة الرئيسية
    "/api/health",      # نقطة صحّة (إن وجدت)
    "/dashboard",       # صفحة لوحة
    "/search?q=test"    # مثال على استعلام
]

# كم طلب يرسل كل دورة (خليها صغيرة: 1-8)
REQUESTS_PER_RUN = 5

# ثواني الانتظار العشوائي بين الطلبات داخل نفس الجولة
MIN_INTERVAL_BETWEEN_REQS = 0.5
MAX_EXTRA_SLEEP = 1.5

# مهلة الطلب بالثواني
REQUEST_TIMEOUT = 15

# مسار ملف اللوق
LOG_FILE = "traffic.log"

# ============================================

# إعداد اللوج
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G970F)",
    "curl/7.68.0"
]

async def do_request(session: aiohttp.ClientSession, path: str):
    # يبني الرابط الصحيح
    if path.startswith("/"):
        url = BASE_URL.rstrip("/") + path
    else:
        url = BASE_URL.rstrip("/") + "/" + path

    # نضيف باراميتر عشوائي أحياناً لتفادي الكاش
    if random.random() < 0.3:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}_r={int(time.time() * 1000)}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"
    }

    start = time.perf_counter()
    try:
        async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            try:
                content = await resp.read()
                size = len(content)
            except Exception:
                size = 0
            elapsed = (time.perf_counter() - start)
            logging.info(f"REQ GET {path} -> {resp.status} ({elapsed:.2f}s) size={size}")
    except Exception as e:
        elapsed = (time.perf_counter() - start)
        logging.warning(f"ERR GET {path} -> {e} ({elapsed:.2f}s)")

async def run_once():
    logging.info("Starting run_once")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(REQUESTS_PER_RUN):
            path = random.choice(ENDPOINTS)
            tasks.append(do_request(session, path))
            # انتظار صغير عشوائي حتى لا تكون الزيارات متزامنة
            await asyncio.sleep(MIN_INTERVAL_BETWEEN_REQS + random.random() * MAX_EXTRA_SLEEP)
        # ننتظر اكتمال كل الطلبات
        await asyncio.gather(*tasks, return_exceptions=True)
    logging.info("Run complete")

def schedule_every_30_minutes():
    scheduler = AsyncIOScheduler(timezone="UTC")
    # شغل أول جولة فوراً ثم كل 30 دقيقة
    scheduler.add_job(lambda: asyncio.create_task(run_once()), "interval", minutes=30, next_run_time=datetime.now())
    scheduler.start()
    logging.info("Scheduled traffic simulator every 30 minutes")

async def main():
    logging.info("Traffic simulator starting")
    # اختبار بسيط قبل الجدولة للتأكد من أن BASE_URL متاحة
    if not (BASE_URL.startswith("http://") or BASE_URL.startswith("https://")):
        logging.error("BASE_URL must start with http:// or https://. Exiting.")
        print("ERROR: عدّل BASE_URL في traffic_simulator.py إلى رابط موقعك وابدأ من جديد.")
        return

    # محاولة اتصال بسيط الآن
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, timeout=REQUEST_TIMEOUT) as resp:
                logging.info(f"Initial GET {BASE_URL} -> {resp.status}")
    except Exception as e:
        logging.warning(f"Initial GET failed: {e}")

    schedule_every_30_minutes()

    # نبقي البوت شغالاً في حلقة لا نهائية
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Traffic simulator stopping")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as ex:
        logging.exception("Unhandled exception, exiting")
