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
from telegram.ext.filters import MessageFilter  # For the custom filter

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

# NEW STATE for /user_m command
USER_M_WAITING_FOR_MESSAGE = 30

# IDs
SPECIAL_USER_ID = 77655677655
AUTHORIZED_USER_ID = 6177929931

# JSON
MUTED_USERS_FILE = 'muted_users.json'
USERS_FILE = 'users.json'

MAIN_MENU_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت', 'حساب درجتك بلبلوك']
]

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

# Load data
muted_users = load_muted_users()
known_users = load_users()

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

    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    logger.info(f"User {user.username or user_id} used /start")

    if user_id == SPECIAL_USER_ID:
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

# =============== NEW: /user_m <userid> command ===============
# 1) We define the command to parse the target user ID
async def user_m_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Usage: /user_m <userid>
    Bot will ask for a message and then send it to that user.
    """
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /user_m <userid>")
        return ConversationHandler.END

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be an integer.")
        return ConversationHandler.END

    # Store the target user ID in user_data so we can retrieve it later
    context.user_data['target_user_id'] = target_id

    # Prompt the authorized user for a message
    await update.message.reply_text(
        f"ستقوم بإرسال رسالة إلى {target_id}. اكتب الرسالة الآن:",
        reply_markup=ReplyKeyboardRemove()
    )
    return USER_M_WAITING_FOR_MESSAGE

# 2) We define the handler that actually sends the message
async def user_m_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("لم يتم العثور على نص للرسالة!")
        return ConversationHandler.END

    # Retrieve target user ID
    target_id = context.user_data.get('target_user_id')
    if not target_id:
        await update.message.reply_text("لم أجد user_id! أعد العملية.")
        return ConversationHandler.END

    # Attempt to send message
    try:
        await context.bot.send_message(chat_id=target_id, text=text)
        await update.message.reply_text(f"تم إرسال رسالتك إلى {target_id} بنجاح!")
    except Exception as e:
        logger.error(f"Failed sending message to {target_id}: {e}")
        await update.message.reply_text("حصل خطأ أثناء إرسال الرسالة.")
    return ConversationHandler.END
# =============================================================

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

# ========== HIGHEST-PRIORITY HANDLER FOR MUTED USERS (Custom Filter) ==========

class MuteFilter(MessageFilter):
    """
    Custom message filter that returns True if the message is from a muted user.
    This is evaluated at runtime for each update, catching newly muted users.
    """
    def filter(self, message):
        if message.from_user is None:
            return False  # e.g., channel post or no user
        return message.from_user.id in muted_users

async def handle_muted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called if MuteFilter is True. Notifies AUTHORIZED_USER_ID about
    the muted user's attempt, and tells the user they're muted.
    """
    user = update.effective_user
    if not user:
        return  # Possibly a channel post, so do nothing.

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

    # /user_m conversation
    user_m_conv = ConversationHandler(
        entry_points=[CommandHandler('user_m', user_m_command)],
        states={
            USER_M_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_m_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # Register conversation handlers
    app.add_handler(conv_handler)
    app.add_handler(user_id_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(user_m_conv)

    # Register commands
    app.add_handler(CommandHandler('muteid', muteid_command))
    app.add_handler(CommandHandler('unmuteid', unmuteid_command))
    app.add_handler(CommandHandler('mutelist', mutelist_command))

    # Fallback for anything else
    app.add_handler(MessageHandler(filters.ALL, default_handler))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("Running bot with polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
