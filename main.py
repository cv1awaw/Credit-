import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for ConversationHandler
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT = range(3)

# Define additional states for /user_id command
USER_ID_WAITING_FOR_MESSAGE = 3

# Special User IDs
SPECIAL_USER_ID = 77655677655  # User to receive messages from /user_id command
AUTHORIZED_USER_ID = 6177929931  # User authorized to use /user_id command

# Keyboard layout
REPLY_KEYBOARD = [['حساب غياب النظري', 'حساب غياب العملي']]
MAIN_MENU_KEYBOARD = [['العودة للقائمة الرئيسية']]

# Message Constants
WELCOME_MESSAGE_DEFAULT = (
    "السلام عليكم \n"
    "البوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
    "ارسل /start اذا البوت بقى ما قبل يشتغل بوحدة من الخيارات"
)
WELCOME_MESSAGE_SPECIAL = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
REQUEST_THEORETICAL_CREDIT = "ارسل كردت مادة النظري"
REQUEST_PRACTICAL_CREDIT = "ارسل ركدت العملي"
INVALID_CHOICE_MESSAGE = "اختيار غير معروف. الرجاء الاختيار من الأزرار."
INVALID_NUMBER_MESSAGE = "الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية."
NOT_AUTHORIZED_MESSAGE = "You are not authorized to use this command."
USER_ID_PROMPT_MESSAGE = "Please send your message."
MESSAGE_SENT_CONFIRMATION = "Message sent: {text}"
MESSAGE_SEND_FAILURE = "Message didn't send. Please try again later."
CANCEL_MESSAGE = (
    "تم إلغاء العملية. للبدء من جديد، ارسل /start"
)
HELP_MESSAGE = (
    "هنا بعض الأوامر التي يمكنك استخدامها:\n"
    "/start - بدء المحادثة مع البوت\n"
    "/user_id - إرسال رسالة مخصصة للمستخدم الخاص\n"
    "/cancel - إلغاء العملية الحالية"
)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    # Log the user ID for debugging
    logger.info(f"User {user.username or 'No Username'} with ID {user_id} started the bot.")

    if user_id == SPECIAL_USER_ID:
        # Personalized welcome message for the special user
        welcome_message = WELCOME_MESSAGE_SPECIAL
        logger.info(f"Sending personalized message to user ID {user_id}.")
    else:
        # Default welcome message for other users
        welcome_message = WELCOME_MESSAGE_DEFAULT
        logger.info(f"Sending default message to user ID {user_id}.")

    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOOSING_OPTION

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE)

# Handler for choosing option
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            REQUEST_THEORETICAL_CREDIT,
            reply_markup=ReplyKeyboardMarkup(
                MAIN_MENU_KEYBOARD, resize_keyboard=True, one_time_keyboard=True
            )
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            REQUEST_PRACTICAL_CREDIT,
            reply_markup=ReplyKeyboardMarkup(
                MAIN_MENU_KEYBOARD, resize_keyboard=True, one_time_keyboard=True
            )
        )
        return GET_PRACTICAL_CREDIT

    else:
        await update.message.reply_text(
            INVALID_CHOICE_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(
                REPLY_KEYBOARD, resize_keyboard=True
            )
        )
        return CHOOSING_OPTION

# Handler for theoretical credit input
async def theoretical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        return await start(update, context)

    try:
        credit = float(text)
        result = credit * 8 * 0.23
        await update.message.reply_text(f"النتيجة: {result}")
        return await start(update, context)
    except ValueError:
        await update.message.reply_text(INVALID_NUMBER_MESSAGE)
        return GET_THEORETICAL_CREDIT

# Handler for practical credit input
async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        return await start(update, context)

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        await update.message.reply_text(f"النتيجة: {result}")
        return await start(update, context)
    except ValueError:
        await update.message.reply_text(INVALID_NUMBER_MESSAGE)
        return GET_PRACTICAL_CREDIT

# Handler for /user_id command
async def user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    logger.info(f"User {user.username or 'No Username'} with ID {user_id} invoked /user_id command.")

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text(NOT_AUTHORIZED_MESSAGE)
        return ConversationHandler.END

    await update.message.reply_text(
        USER_ID_PROMPT_MESSAGE,
        reply_markup=ReplyKeyboardRemove()
    )
    return USER_ID_WAITING_FOR_MESSAGE

# Handler for processing the user's message in /user_id conversation
async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id

    if text:
        try:
            await context.bot.send_message(chat_id=SPECIAL_USER_ID, text=text)
            await update.message.reply_text(
                MESSAGE_SENT_CONFIRMATION.format(text=text),
                reply_markup=ReplyKeyboardMarkup(
                    REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
                )
            )
            logger.info(f"Message from user ID {user_id} sent to SPECIAL_USER_ID {SPECIAL_USER_ID}.")
        except Exception as e:
            logger.error(f"Failed to send message to SPECIAL_USER_ID {SPECIAL_USER_ID}: {e}")
            await update.message.reply_text(MESSAGE_SEND_FAILURE)
    else:
        await update.message.reply_text(MESSAGE_SEND_FAILURE)

    return ConversationHandler.END

# Fallback handler for /user_id conversation
async def user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        CANCEL_MESSAGE,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Fallback handler for main conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        CANCEL_MESSAGE,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Default handler for any other messages
async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    reply_keyboard = REPLY_KEYBOARD

    if user_id == SPECIAL_USER_ID:
        welcome_message = WELCOME_MESSAGE_SPECIAL
    else:
        welcome_message = WELCOME_MESSAGE_DEFAULT

    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        )
    )

# Error handler to catch exceptions
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("حدث خطأ ما. يرجى المحاولة لاحقًا.")

def main():
    # Retrieve the bot token from environment variables
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set.")
        exit(1)

    # Initialize the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Define the main ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_OPTION: [
                MessageHandler(
                    filters.Regex('^(حساب غياب النظري|حساب غياب العملي)$'), choice_handler
                )
            ],
            GET_THEORETICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, theoretical_credit)
            ],
            GET_PRACTICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, practical_credit)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    # Define the ConversationHandler for /user_id command
    user_id_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('user_id', user_id_command)],
        states={
            USER_ID_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', user_cancel)],
        allow_reentry=True
    )

    # Define handlers for additional commands
    help_handler = CommandHandler('help', help_command)

    # Define a general MessageHandler to handle all other messages
    general_handler = MessageHandler(filters.ALL & ~filters.COMMAND, default_handler)

    # Add handlers to the application
    application.add_handler(conv_handler)
    application.add_handler(user_id_conv_handler)
    application.add_handler(help_handler)
    application.add_handler(general_handler)  # This should be added last

    # Add the error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
