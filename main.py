import logging
import os
import json
import asyncio
from datetime import datetime, timedelta

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.ext.filters import MessageFilter

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT, SEND_MESSAGE = range(4)
BLOK_MATERIA, BLOK_TOTAL, BLOK_TAKEN = range(5, 8)
USER_ID_WAITING_FOR_MESSAGE = 10
BROADCAST_ASK_MESSAGE, BROADCAST_CONFIRMATION = range(20, 22)

# For /user_m
USER_M_WAITING_FOR_MESSAGE = 30

# For /hey
HEY_WAITING_FOR_MESSAGE = 999

# IDs
SPECIAL_USER_ID = 77655677655
AUTHORIZED_USER_ID = 6177929931

# JSON
MUTED_USERS_FILE = 'muted_users.json'
USERS_FILE = 'users.json'
WELCOME_MSGS_FILE = 'welcome_msgs.json'  # store custom welcomes

MAIN_MENU_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت', 'حساب درجتك بلبلوك']
]

def load_override_welcomes():
    """Load custom welcome messages { user_id: "message" }."""
    if os.path.exists(WELCOME_MSGS_FILE):
        with open(WELCOME_MSGS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)  # { "123": "some msg" }
                return {int(k): v for k, v in data.items()}
            except json.JSONDecodeError:
                return {}
    return {}

def save_override_welcomes(mapping):
    """Save { user_id: "message" } as { "123": "some msg" } to JSON."""
    to_save = {str(k): v for k, v in mapping.items()}
    with open(WELCOME_MSGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(to_save, f, ensure_ascii=False)

def load_muted_users():
    if os.path.exists(MUTED_USERS_FILE):
        with open(MUTED_USERS_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_muted_users(muted):
    with open(MUTED_USERS_FILE, 'w') as f:
        json.dump(list(muted), f)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError):
                return {}
    return {}

def save_users(users_dict):
    with open(USERS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in users_dict.items()}, f)

# Global sets/dicts
muted_users = load_muted_users()
known_users = load_users()  # Now stores {user_id: last_activity_timestamp}
override_welcome_messages = load_override_welcomes()

def log_user_activity(user_id):
    """Update user's last activity timestamp"""
    known_users[user_id] = datetime.now().isoformat()
    save_users(known_users)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Whenever user sends /start, show the custom or default welcome,
    then go to CHOOSING_OPTION.
    """
    user = update.effective_user
    user_id = user.id

    log_user_activity(user_id)
    
    logger.info(f"User {user.username or user_id} used /start - Full message: {update.message.text}")

    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    if user_id not in known_users:
        known_users[user_id] = datetime.now().isoformat()
        save_users(known_users)

    if user_id in override_welcome_messages:
        welcome_text = override_welcome_messages[user_id]
    elif user_id == SPECIAL_USER_ID:
        welcome_text = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
    else:
        welcome_text = (
            "السلام عليكم \nالبوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اهلا وسهلا!"
        )

    await update.message.reply_text(welcome_text)
    await asyncio.sleep(0.3)

    await show_main_menu(update, context)
    return CHOOSING_OPTION

async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} selected option: {text}")

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة النظري (مثال: 3.0).\n\n"
            "أو اختر 'العودة للقائمة الرئيسية' في الأسفل:",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة العملي (مثال: 1.5).\n\n"
            "أو اختر 'العودة للقائمة الرئيسية' في الأسفل:",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return GET_PRACTICAL_CREDIT

    elif text == 'ارسل رسالة لصاحب البوت':
        await update.message.reply_text(
            "يمكنك إرسال رسالتك الآن، أو اختر العودة للقائمة الرئيسية:",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SEND_MESSAGE

    elif text == 'حساب درجتك بلبلوك':
        await update.message.reply_text(
            "شكد المادة عليها بلبلوك؟ (اكتب رقم فقط)",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return BLOK_MATERIA

    else:
        await update.message.reply_text("خيار غير معروف!")
        await show_main_menu(update, context)
        return CHOOSING_OPTION

async def theoretical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered theoretical credit: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.2352941176
        formatted_result = f"{result:.2f}"
        await update.message.reply_text(f"غيابك للنظري هو: {formatted_result}")
    except ValueError:
        await update.message.reply_text(
            "الرجاء إدخال رقم فقط.\nمثال: 3.0 أو 2.5\n"
            "أو اختر العودة للقائمة الرئيسية."
        )
        return GET_THEORETICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered practical credit: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        formatted_result = f"{result:.2f}"
        await update.message.reply_text(f"غيابك للعملي هو: {formatted_result}")
    except ValueError:
        await update.message.reply_text(
            "الرجاء إدخال رقم فقط.\nمثال: 1 أو 1.5\n"
            "أو اختر العودة للقائمة الرئيسية."
        )
        return GET_PRACTICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# بلبلوك
async def blok_materia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered blok materia: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        context.user_data['blok_materia'] = float(text)
        await update.message.reply_text(
            "شكد الدرجة الكلية لهذي المادة؟ (اكتب رقم فقط)",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return BLOK_TOTAL
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return BLOK_MATERIA

async def blok_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered blok total: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        context.user_data['blok_total'] = float(text)
        await update.message.reply_text(
            "شكد خذيت؟ (اكتب رقم فقط)",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return BLOK_TAKEN
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return BLOK_TOTAL

async def blok_taken(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered blok taken: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        taken = float(text)
        materia_val = context.user_data.get('blok_materia', 0)
        total_val = context.user_data.get('blok_total', 1)
        result = (materia_val * taken) / total_val
        formatted_result = f"{result:.2f}"
        await update.message.reply_text(f"درجتك بلبلوك هي: {formatted_result}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return BLOK_TAKEN

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# ارسل رسالة لصاحب البوت
async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} sent message to bot owner: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    user_id = user.id
    username = user.username or f"ID {user_id}"

    if text:
        try:
            formatted = f"رسالة من @{username} (ID: {user_id}):\n\n{text}"
            await context.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=formatted)
            await update.message.reply_text("تم إرسال الرسالة بنجاح.")
        except Exception as e:
            logger.error(f"Failed to forward message: {e}")
            await update.message.reply_text("حصل خطأ أثناء إرسال الرسالة. حاول مرة أخرى.")
    else:
        await update.message.reply_text("لم يتم العثور على نص للرسالة.")

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# New /active command
async def active_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    total_users = len(known_users)
    
    # Calculate daily active users
    daily_active = 0
    now = datetime.now()
    for last_active in known_users.values():
        try:
            last_active_time = datetime.fromisoformat(last_active)
            if (now - last_active_time) < timedelta(hours=24):
                daily_active += 1
        except:
            continue

    response = (
        f"📊 Bot Usage Statistics:\n\n"
        f"• Total Users: {total_users}\n"
        f"• Active Today: {daily_active}"
    )
    
    await update.message.reply_text(response)

# Updated help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == AUTHORIZED_USER_ID:
        admin_help_text = (
            "🚀 أوامر المشرف:\n\n"
            "/help - إظهار هذه القائمة.\n"
            "/start - بدء المحادثة أو عرض القائمة.\n"
            "/active - إظهار إحصائيات الاستخدام\n"
            "/muteid <userid> - كتم مستخدم.\n"
            "/unmuteid <userid> - إلغاء كتم مستخدم.\n"
            "/mutelist - عرض المكتومين.\n"
            "/user_id - إرسال رسالة إلى SPECIAL_USER_ID.\n"
            "/user_m <userid> - إرسال رسالة إلى user_id.\n"
            "/hey <userid> - تعيين رسالة ترحيب مخصصة.\n"
            "/hey_r <userid> - حذف رسالة الترحيب المخصصة.\n"
            "/new - إرسال رسالة جماعية لجميع المستخدمين.\n"
            "/cancel - إلغاء العملية الحالية.\n"
        )
        await update.message.reply_text(admin_help_text)
    else:
        user_help_text = (
            "مرحباً! أنا بوت للمساعدة.\n"
            "الأوامر المتاحة:\n"
            "/start - بدء المحادثة أو عرض القائمة.\n"
            "/help - عرض هذه الرسالة.\n"
        )
        await update.message.reply_text(user_help_text)

# ... (keep all other existing functions the same, just add log_user_activity() calls where needed)

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return

    # Remove webhook if any, so we can do polling
    try:
        bot = Bot(token=BOT_TOKEN)
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted.")
    except Exception as e:
        logger.warning(f"No webhook to delete or error: {e}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add new command handler
    app.add_handler(CommandHandler('active', active_command))

    # ... (rest of the main function remains the same)

if __name__ == '__main__':
    main()
