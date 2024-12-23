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

# Define constants for user IDs
SPECIAL_USER_ID = 6733595501  # User to receive messages from /user_id command
AUTHORIZED_USER_ID = 6177929931  # User authorized to use /user_id command

# Keyboard layout
REPLY_KEYBOARD = [['حساب غياب النظري', 'حساب غياب العملي']]

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    # Log the user ID for debugging
    logger.info(f"User {user.username or 'No Username'} with ID {user_id} started the bot.")

    if user_id == SPECIAL_USER_ID:
        # Personalized welcome message for the special user
        welcome_message = (
            "اهلا زهراء في البوت مالتي 🌹\n"
            "اتمنى تستفادين منه ^^\n\n"
            "اضغطي /start حتى يشتغل البوت "
        )
        logger.info(f"Sending personalized message to user ID {user_id}.")
    else:
        # Default welcome message for other users
        welcome_message = (
            "السلام عليكم \n"
            "البوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اضغط /start حتى يشتغل البوت "
        )
        logger.info(f"Sending default message to user ID {user_id}.")

    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOOSING_OPTION

# Handler for choosing option
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            "ارسل كردت مادة النظري",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']], resize_keyboard=True, one_time_keyboard=True
            )
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            "ارسل كردت العملي",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']], resize_keyboard=True, one_time_keyboard=True
            )
        )
        return GET_PRACTICAL_CREDIT

    else:
        await update.message.reply_text(
            "اختيار غير معروف. الرجاء الاختيار من الأزرار.",
            reply_markup=ReplyKeyboardMarkup(
                REPLY_KEYBOARD, resize_keyboard=True
            )
        )
        return CHOOSING_OPTION

# Handler for theoretical credit input
async def theoretical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        await update.message.reply_text(
            "تم الرجوع إلى القائمة الرئيسية.",
            reply_markup=ReplyKeyboardMarkup(
                REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
            )
        )
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.23
        await update.message.reply_text(f"النتيجة: {result}")
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية.")
        return GET_THEORETICAL_CREDIT

    # After processing, show the main menu again
    await update.message.reply_text(
        "اختر خيارًا آخر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOOSING_OPTION

# Handler for practical credit input
async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        await update.message.reply_text(
            "تم الرجوع إلى القائمة الرئيسية.",
            reply_markup=ReplyKeyboardMarkup(
                REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
            )
        )
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        await update.message.reply_text(f"النتيجة: {result}")
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية.")
        return GET_PRACTICAL_CREDIT

    # After processing, show the main menu again
    await update.message.reply_text(
        "اختر خيارًا آخر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOOSING_OPTION

# Handler for /user_id command
async def user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    logger.info(f"User {user.username or 'No Username'} with ID {user_id} invoked /user_id command.")

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Extract the message from the command arguments
    if context.args:
        message = ' '.join(context.args)
        try:
            await context.bot.send_message(chat_id=SPECIAL_USER_ID, text=message)
            await update.message.reply_text(f"The message has been sent to user ID {SPECIAL_USER_ID}.")
            logger.info(f"Message from user ID {user_id} sent to SPECIAL_USER_ID {SPECIAL_USER_ID}.")
        except Exception as e:
            logger.error(f"Failed to send message to SPECIAL_USER_ID {SPECIAL_USER_ID}: {e}")
            await update.message.reply_text("Failed to send the message. Please try again later.")
    else:
        await update.message.reply_text("Please provide a message to send. Usage: /user_id Your message here")

# Fallback handler for main conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "تم إلغاء العملية. للبدء من جديد، ارسل /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Default handler for any other messages
async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if user_id == SPECIAL_USER_ID:
        welcome_message = (
            "اهلا زهراء في البوت مالتي 🌹\n"
            "اتمنى تستفادين منه ^^\n\n"
            "اضغطي /start حتى يشتغل البوت "
        )
    else:
        welcome_message = (
            "السلام عليكم \n"
            "البوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اضغط /start حتى يشتغل البوت "
        )

    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )

def main():
    # Retrieve the bot token from environment variables
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set.")
        exit(1)

    # Initialize the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Define the main ConversationHandler for /start command
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

    # Define the CommandHandler for /user_id command
    user_id_handler = CommandHandler('user_id', user_id_command)

    # Define a general MessageHandler to handle all other non-command messages
    general_handler = MessageHandler(filters.ALL & ~filters.COMMAND, default_handler)

    # Add handlers to the application in the correct order
    application.add_handler(conv_handler)
    application.add_handler(user_id_handler)
    application.add_handler(general_handler)  # This should be added last to avoid overriding

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
