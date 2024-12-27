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

# Set logging to INFO for less verbosity
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the main conversation
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT, SEND_MESSAGE = range(4)

# States for بلبلوك flow
BLOK_MATERIA, BLOK_TOTAL, BLOK_TAKEN = range(5, 8)

# This extra state is for the /user_id command flow
USER_ID_WAITING_FOR_MESSAGE = 10

# IDs
SPECIAL_USER_ID = 77655677655    # Example special user
AUTHORIZED_USER_ID = 6177929931  # Person who can mute/unmute

# Path to the muted users file
MUTED_USERS_FILE = 'muted_users.json'

# Main menu keyboard
MAIN_MENU_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت', 'حساب درجتك بلبلوك']
]

# Utility functions for loading/saving muted users
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

# Initialize the set of muted users
muted_users = load_muted_users()

# Helper function to show the main menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the main menu keyboard."""
    await update.message.reply_text(
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    # Check for mute
    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    logger.info(f"User {user.username or user_id} started the bot.")

    # Personalized vs default message
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
            "يرجى إرسال رسالتك الآن.",
            reply_markup=ReplyKeyboardRemove()
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

# Handle theoretical credit
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

# Handle practical credit
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
        blok_total_value = context.user_data.get('blok_total', 1)  # Avoid zero-division

        result = (blok_materia_value * blok_taken_value) / blok_total_value
        await update.message.reply_text(f"درجتك بلبلوك هي: {result}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")

    await show_main_menu(update, context)
    return CHOOSING_OPTION

# Handler to send a message to the bot owner
async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
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

# /user_id command (only for AUTHORIZED_USER_ID)
async def user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
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

# Mute a user
async def muteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
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

# Unmute a user
async def unmuteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
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

# Show mute list
async def mutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized.")
        return

    if muted_users:
        text = "\n".join(str(u) for u in muted_users)
        await update.message.reply_text("Muted users:\n" + text)
    else:
        await update.message.reply_text("No muted users.")

# Fallback handler for main conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

# Fallback for /user_id conversation
async def user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("ألغيت العملية.")
    return ConversationHandler.END

# Default handler for out-of-context messages
async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in muted_users:
        await update.message.reply_text("⚠️ أنت مكتوم.")
        return

    await update.message.reply_text(
        "لم أفهم رسالتك، استخدم الأزرار في الأسفل أو اكتب /start للبدء من جديد."
    )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("عذراً حصل خطأ. حاول مجدداً.")

def main():
    # Retrieve token
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return

    # Build application
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

            # Blok calculation
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
        allow_reentry=True
    )

    # /user_id conversation
    user_id_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('user_id', user_id_command)],
        states={
            USER_ID_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', user_cancel)],
        allow_reentry=False
    )

    # Register handlers
    application.add_handler(conv_handler)
    application.add_handler(user_id_conv_handler)
    application.add_handler(CommandHandler('muteid', muteid_command))
    application.add_handler(CommandHandler('unmuteid', unmuteid_command))
    application.add_handler(CommandHandler('mutelist', mutelist_command))

    # Catch any other messages not handled by the conv_handler
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, default_handler))

    # Log errors
    application.add_error_handler(error_handler)

    # Run bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
