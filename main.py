import logging
import os
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Set logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for main conversation
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT, SEND_MESSAGE = range(4)
# States for بلبلوك flow
BLOK_MATERIA, BLOK_TOTAL, BLOK_TAKEN = range(5, 8)
# State for /user_id conversation
USER_ID_WAITING_FOR_MESSAGE = 10
# States for broadcast
BROADCAST_ASK_MESSAGE, BROADCAST_CONFIRMATION = range(20, 22)

# IDs
SPECIAL_USER_ID = 77655677655
AUTHORIZED_USER_ID = 6177929931

# Files
MUTED_USERS_FILE = 'muted_users.json'
USERS_FILE = 'users.json'

# Main menu keyboard
MAIN_MENU_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت', 'حساب درجتك بلبلوك']
]

# ------------------ Load/Save Data ------------------ #
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

# ------------------ Shared Helpers ------------------ #
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

# ------------------ /start ------------------ #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    # Save user so we can broadcast later
    if user_id not in known_users:
        known_users.add(user_id)
        save_users(known_users)

    # Check if muted
    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    logger.info(f"User {user.username or user_id} started the bot.")

    # Greet
    if user_id == SPECIAL_USER_ID:
        welcome_message = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
    else:
        welcome_message = (
            "السلام عليكم \nالبوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اهلا وسهلا!"
        )

    await update.message.reply_text(welcome_message)
    await show_main_menu(update, context)
    return CHOOSING_OPTION

# ------------------ Main Conversation Handlers ------------------ #
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            "ارسل كردت مادة النظري",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            "ارسل ركدت العملي",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                resize_keyboard=True,
                one_time_keyboard=True
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
            "شكد المادة عليها بلبلوك؟",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                resize_keyboard=True,
                one_time_keyboard=True
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
        await update.message.reply_text("الرجاء إدخال رقم صالح.")

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
        await update.message.reply_text("الرجاء إدخال رقم صالح.")

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# بلبلوك flow
async def blok_materia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        context.user_data['blok_materia'] = float(text)
        await update.message.reply_text(
            "شكد الدرجة الكلية لهذي المادة؟",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                resize_keyboard=True,
                one_time_keyboard=True
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
            "شكد خذيت؟",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']],
                resize_keyboard=True,
                one_time_keyboard=True
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

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# Send a message to bot owner
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

# /user_id (only for AUTHORIZED_USER_ID)
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

# ------------------ BROADCAST via /new ------------------ #
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text(
        "ما هي الرسالة التي تريد إرسالها للجميع؟\n\n"
        "(اكتب /cancel للإلغاء)",
        reply_markup=ReplyKeyboardRemove()
    )
    return BROADCAST_ASK_MESSAGE

async def broadcast_ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # We capture ANY input (including slashes) except exactly /cancel
    text = update.message.text
    context.user_data['broadcast_msg'] = text

    # Confirm
    confirm_keyboard = [["نعم، إرسال", "إلغاء"]]
    await update.message.reply_text(
        f"هل أنت متأكد من إرسال هذه الرسالة؟\n\n«{text}»",
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

# ------------------ Mute/Unmute/Mutelist ------------------ #
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

# ------------------ Fallbacks & Default ------------------ #
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in muted_users:
        await update.message.reply_text("⚠️ أنت مكتوم.")
        return

    await update.message.reply_text(
        "لم أفهم رسالتك، استخدم الأزرار في الأسفل أو اكتب /start للبدء من جديد."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("عذراً حصل خطأ. حاول مجدداً.")

# ------------------ main() ------------------ #
def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

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
    user_id_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('user_id', user_id_command)],
        states={
            USER_ID_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # Broadcast conversation
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', broadcast_start)],
        states={
            # capture ANY input except exactly /cancel
            BROADCAST_ASK_MESSAGE: [
                MessageHandler(
                    filters.ALL & ~filters.Regex('^/cancel$'),
                    broadcast_ask_message
                )
            ],
            BROADCAST_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirmation)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=False
    )

    # Register conversation handlers
    application.add_handler(conv_handler)
    application.add_handler(user_id_conv_handler)
    application.add_handler(broadcast_conv_handler)

    # Register commands
    application.add_handler(CommandHandler('muteid', muteid_command))
    application.add_handler(CommandHandler('unmuteid', unmuteid_command))
    application.add_handler(CommandHandler('mutelist', mutelist_command))

    # Catch unhandled
    application.add_handler(MessageHandler(filters.ALL, default_handler))

    # Errors
    application.add_error_handler(error_handler)

    # Run
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
