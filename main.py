import logging
import os
import json
import asyncio

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

# NEW STATES for /hey command
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

# =============== Functions to load/save custom welcome messages ===============
def load_override_welcomes():
    """
    Load dictionary { user_id_str: custom_message } from JSON.
    We'll convert user_id_str to int at runtime.
    """
    if os.path.exists(WELCOME_MSGS_FILE):
        with open(WELCOME_MSGS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # data is { "123456": "custom welcome..." }
                # we convert to { 123456: "custom welcome..." }
                return {int(k): v for k, v in data.items()}
            except json.JSONDecodeError:
                return {}
    return {}

def save_override_welcomes(mapping):
    """
    Save dictionary { user_id: custom_message } to JSON as { "user_id": "msg" }
    """
    to_save = {str(k): v for k, v in mapping.items()}
    with open(WELCOME_MSGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(to_save, f, ensure_ascii=False)

# =============== Load data ===============
def load_muted_users():
    if os.path.exists(MUTED_USERS_FILE):
        with open(MUTED_USERS_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_muted_users(muted_users):
    with open(MUTED_USERS_FILE, 'w') as f:
        json.dump(list(muted_users), f)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f)

muted_users = load_muted_users()
known_users = load_users()
override_welcome_messages = load_override_welcomes()  # { int_user_id: "message" }

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
    user = update.effective_user
    user_id = user.id

    # Record user
    if user_id not in known_users:
        known_users.add(user_id)
        save_users(known_users)

    # Check if muted
    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    logger.info(f"User {user.username or user_id} used /start")

    # 1) Check if there's a custom welcome override
    if user_id in override_welcome_messages:
        welcome = override_welcome_messages[user_id]
    # 2) Otherwise, check if user is the SPECIAL_USER_ID
    elif user_id == SPECIAL_USER_ID:
        welcome = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
    else:
        welcome = (
            "السلام عليكم \nالبوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اهلا وسهلا!"
        )

    await update.message.reply_text(welcome)
    await asyncio.sleep(0.3)
    await show_main_menu(update, context)

    return CHOOSING_OPTION

async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة النظري (مثال: 3.0)."
            "\n\nأو اختر 'العودة للقائمة الرئيسية' في الأسفل:",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة العملي (مثال: 1.5)."
            "\n\nأو اختر 'العودة للقائمة الرئيسية' في الأسفل:",
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
    text = (update.message.text or "").strip()

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.23
        await update.message.reply_text(f"غيابك للنظري هو: {result}")
    except ValueError:
        await update.message.reply_text(
            "الرجاء إدخال رقم فقط.\nمثال: 3.0 أو 2.5\nأو اختر العودة للقائمة الرئيسية."
        )
        return GET_THEORETICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        await update.message.reply_text(f"غيابك للعملي هو: {result}")
    except ValueError:
        await update.message.reply_text(
            "الرجاء إدخال رقم فقط.\nمثال: 1 أو 1.5\nأو اختر العودة للقائمة الرئيسية."
        )
        return GET_PRACTICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# بلبلوك
async def blok_materia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
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
    text = (update.message.text or "").strip()
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
    text = (update.message.text or "").strip()
    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        blok_taken_value = float(text)
        blok_materia_value = context.user_data.get('blok_materia', 0)
        blok_total_value = context.user_data.get('blok_total', 1)
        result = (blok_materia_value * blok_taken_value) / blok_total_value
        await update.message.reply_text(f"درجتك بلبلوك هي: {result}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return BLOK_TAKEN

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# ارسل رسالة لصاحب البوت
async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    user = update.effective_user
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

# /user_id -> message to SPECIAL_USER_ID
async def user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Send your message for the SPECIAL_USER_ID:",
        reply_markup=ReplyKeyboardRemove()
    )
    return USER_ID_WAITING_FOR_MESSAGE

async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    user = update.effective_user

    if text:
        try:
            msg = f"Message from {user.username or user.id} (ID: {user.id}):\n{text}"
            await context.bot.send_message(chat_id=SPECIAL_USER_ID, text=msg)
            await update.message.reply_text("تم إرسال رسالتك بنجاح!")
        except Exception as e:
            logger.error(f"Failed sending message to SPECIAL_USER_ID: {e}")
            await update.message.reply_text("حصل خطأ أثناء إرسال الرسالة.")
    else:
        await update.message.reply_text("لا يوجد نص في الرسالة!")
    return ConversationHandler.END

# /hey <userid> -> set custom welcome
HEY_WAITING_FOR_MESSAGE = 999

async def hey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /hey <userid>
    """
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /hey <userid>")
        return ConversationHandler.END

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be an integer.")
        return ConversationHandler.END

    context.user_data['hey_target_id'] = target_id
    await update.message.reply_text(
        f"ستقوم بتغيير الترحيب للمستخدم {target_id}. اكتب الرسالة الآن:",
        reply_markup=ReplyKeyboardRemove()
    )
    return HEY_WAITING_FOR_MESSAGE

async def hey_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the custom welcome text from the authorized user.
    """
    new_msg = (update.message.text or "").strip()
    if not new_msg:
        await update.message.reply_text("لم يتم العثور على نص الرسالة! أعد المحاولة.")
        return ConversationHandler.END

    target_id = context.user_data.get('hey_target_id')
    if not target_id:
        await update.message.reply_text("لم أجد user_id! أعد العملية.")
        return ConversationHandler.END

    override_welcome_messages[target_id] = new_msg
    save_override_welcomes(override_welcome_messages)

    await update.message.reply_text(
        f"تم تغيير رسالة الترحيب للمستخدم {target_id} بنجاح!\n"
        f"الترحيب الجديد: {new_msg}"
    )
    return ConversationHandler.END

# /hey_r <userid> -> remove custom welcome
async def hey_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /hey_r <userid>
    Removes the custom welcome message for that user.
    """
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /hey_r <userid>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be an integer.")
        return

    if target_id in override_welcome_messages:
        del override_welcome_messages[target_id]
        save_override_welcomes(override_welcome_messages)
        await update.message.reply_text(
            f"تم حذف رسالة الترحيب المخصصة للمستخدم {target_id}.\n"
            "الآن سيحصل على الرسالة الافتراضية عند استخدام /start."
        )
    else:
        await update.message.reply_text("هذا المستخدم ليس لديه رسالة ترحيب مخصصة.")

# Broadcast flow
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text(
        "ما هي الرسالة التي تريد إرسالها للجميع؟\n\n(اكتب /cancel للإلغاء)",
        reply_markup=ReplyKeyboardRemove()
    )
    return BROADCAST_ASK_MESSAGE

async def broadcast_ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['broadcast_msg'] = update.message.text

    confirm_keyboard = [["نعم، إرسال", "إلغاء"]]
    await update.message.reply_text(
        f"هل أنت متأكد من إرسال هذه الرسالة؟\n\n«{update.message.text}»",
        reply_markup=ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return BROADCAST_CONFIRMATION

async def broadcast_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == "نعم، إرسال":
        broadcast_msg = context.user_data.get('broadcast_msg', "")
        if not broadcast_msg:
            await update.message.reply_text("لا توجد رسالة للإرسال!")
            return ConversationHandler.END

        sent_count = 0
        for uid in known_users:
            try:
                await context.bot.send_message(chat_id=uid, text=broadcast_msg)
                sent_count += 1
            except Exception as e:
                logger.error(f"Could not send to user {uid}: {e}")

        await update.message.reply_text(f"تم إرسال الرسالة إلى {sent_count} مستخدم/مستخدمين.")
    else:
        await update.message.reply_text("تم الإلغاء.")

    return ConversationHandler.END

# Mute/Unmute/Mutelist commands
async def muteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /muteid <userid>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Provide a valid user ID.")
        return

    if target_id in muted_users:
        await update.message.reply_text("User is already muted.")
    else:
        muted_users.add(target_id)
        save_muted_users(muted_users)
        await update.message.reply_text(f"User {target_id} has been muted.")

async def unmuteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /unmuteid <userid>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Provide a valid user ID.")
        return

    if target_id in muted_users:
        muted_users.remove(target_id)
        save_muted_users(muted_users)
        await update.message.reply_text(f"User {target_id} has been unmuted.")
    else:
        await update.message.reply_text("User is not muted.")

async def mutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized.")
        return

    if muted_users:
        text = "\n".join(str(u) for u in muted_users)
        await update.message.reply_text("Muted users:\n" + text)
    else:
        await update.message.reply_text("No muted users.")

# =================== /help Command ======================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == AUTHORIZED_USER_ID:
        # Show all authorized commands
        admin_help_text = (
            "🚀 أوامر المشرف:\n\n"
            "/help - إظهار هذه القائمة.\n"
            "/start - بدء المحادثة أو عرض القائمة.\n"
            "/muteid <userid> - كتم مستخدم.\n"
            "/unmuteid <userid> - إلغاء كتم مستخدم.\n"
            "/mutelist - عرض المستخدمين المكتومين.\n"
            "/user_id - إرسال رسالة إلى SPECIAL_USER_ID.\n"
            "/user_m <userid> - إرسال رسالة إلى user_id.\n"
            "/hey <userid> - تعيين رسالة ترحيب مخصصة.\n"
            "/hey_r <userid> - حذف رسالة الترحيب المخصصة.\n"
            "/new - إرسال رسالة جماعية لجميع المستخدمين.\n"
            "/cancel - إلغاء العملية الحالية.\n"
        )
        await update.message.reply_text(admin_help_text)
    else:
        # Basic help for normal users
        user_help_text = (
            "مرحباً! أنا بوت للمساعدة.\n"
            "الأوامر المتاحة:\n"
            "/start - بدء المحادثة أو عرض القائمة\n"
            "/help - عرض هذه الرسالة\n"
        )
        await update.message.reply_text(user_help_text)


# ========== HIGHEST-PRIORITY HANDLER FOR MUTED USERS (Custom Filter) ==========

class MuteFilter(MessageFilter):
    """
    Custom message filter that returns True if the message is from a muted user.
    This is evaluated at runtime for each update, catching newly muted users.
    """
    def filter(self, message):
        if message.from_user is None:
            return False
        return message.from_user.id in muted_users

async def handle_muted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    username = user.username or f"ID {user_id}"
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = (first_name + " " + last_name).strip()

    # Notify the authorized user
    notification_message = (
        "⚠️ Muted user tried to interact with the bot:\n\n"
        f"• ID: {user_id}\n"
        f"• Username: @{username}\n"
        f"• Full Name: {full_name if full_name else 'Not provided'}"
    )
    try:
        await context.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=notification_message)
    except Exception as e:
        logger.error(f"Failed to notify admin of muted user attempt: {e}")

    # Respond to the muted user
    await update.message.reply_text("⚠️ أنت مكتوم ولا يمكنك استخدام البوت.")

# ==============================================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id and (user_id in muted_users):
        await update.message.reply_text("⚠️ أنت مكتوم.")
        return

    await update.message.reply_text(
        "لم أفهم رسالتك، استخدم الأزرار في الأسفل أو اكتب /start للبدء من جديد."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("عذراً حصل خطأ. حاول مجدداً.")

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return

    # Remove any leftover webhook if we only do polling
    try:
        bot = Bot(token=BOT_TOKEN)
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted to avoid 409 conflicts.")
    except Exception as e:
        logger.warning(f"No webhook to delete or error: {e}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Highest priority: Mute filter
    mute_filter = MuteFilter()
    app.add_handler(MessageHandler(mute_filter, handle_muted), group=0)

    # Main conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_OPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choice_handler),
            ],
            GET_THEORETICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, theoretical_credit),
            ],
            GET_PRACTICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, practical_credit),
            ],
            SEND_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_handler),
            ],
            BLOK_MATERIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, blok_materia),
            ],
            BLOK_TOTAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, blok_total),
            ],
            BLOK_TAKEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, blok_taken),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # /user_id conversation
    user_id_conv = ConversationHandler(
        entry_points=[CommandHandler('user_id', user_id_command)],
        states={
            USER_ID_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # /new broadcast conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('new', broadcast_start)],
        states={
            BROADCAST_ASK_MESSAGE: [
                MessageHandler(filters.ALL & ~filters.Regex('^/cancel$'), broadcast_ask_message)
            ],
            BROADCAST_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirmation)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # /hey conversation
    hey_conv = ConversationHandler(
        entry_points=[CommandHandler('hey', hey_command)],
        states={
            HEY_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, hey_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # Register conversation handlers
    app.add_handler(conv_handler)
    app.add_handler(user_id_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(hey_conv)

    # Register commands
    app.add_handler(CommandHandler('hey_r', hey_remove_command))
    app.add_handler(CommandHandler('muteid', muteid_command))
    app.add_handler(CommandHandler('unmuteid', unmuteid_command))
    app.add_handler(CommandHandler('mutelist', mutelist_command))
    app.add_handler(CommandHandler('help', help_command))  # <--- Our new /help command

    # Fallback for anything else
    app.add_handler(MessageHandler(filters.ALL, default_handler))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("Running bot with polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
