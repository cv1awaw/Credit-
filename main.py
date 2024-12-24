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
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for ConversationHandler
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT, SEND_MESSAGE_TO_OWNER = range(4)

# Define additional states for /user_id command
USER_ID_WAITING_FOR_MESSAGE = 4

# Special User IDs
SPECIAL_USER_ID = 77655677655  # User to receive messages from /user_id command and owner messages
AUTHORIZED_USER_ID = 6177929931  # User authorized to use /user_id command

# Keyboard layout
REPLY_KEYBOARD = [['حساب غياب النظري', 'حساب غياب العملي'], ['ارسل رسالة لصاحب البوت']]
MAIN_MENU_KEYBOARD = [['العودة للقائمة الرئيسية']]

# Message Constants
WELCOME_MESSAGE_DEFAULT = (
    "السلام عليكم \n"
    "البوت تم تطويره بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
    "أرسل /start إذا البوت لم يبدأ بالعمل وحدد أحد الخيارات."
)
WELCOME_MESSAGE_SPECIAL = "أهلاً زهراء في البوت الخاص بي 🌹\nأتمنى أن تستفيدين منه ^^"
REQUEST_THEORETICAL_CREDIT = "أرسل رصيد مادة النظري."
REQUEST_PRACTICAL_CREDIT = "أرسل رصيد العملي."
REQUEST_OWNER_MESSAGE = "يرجى إرسال رسالتك التي تريد إرسالها إلى صاحب البوت."
INVALID_CHOICE_MESSAGE = "اختيار غير معروف. الرجاء الاختيار من الأزرار."
INVALID_NUMBER_MESSAGE = "الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية."
NOT_AUTHORIZED_MESSAGE = "أنت غير مخول لاستخدام هذا الأمر."
USER_ID_PROMPT_MESSAGE = "يرجى إرسال رسالتك."
MESSAGE_SENT_CONFIRMATION = "تم إرسال رسالتك إلى صاحب البوت. شكرًا لتواصلك!"
MESSAGE_SEND_FAILURE = "فشل في إرسال الرسالة. يرجى المحاولة لاحقًا."
CANCEL_MESSAGE = (
    "تم إلغاء العملية. للبدء من جديد، أرسل /start."
)
HELP_MESSAGE = (
    "هنا بعض الأوامر التي يمكنك استخدامها:\n"
    "/start - بدء المحادثة مع البوت\n"
    "/user_id - إرسال رسالة مخصصة للمستخدم الخاص\n"
    "/cancel - إلغاء العملية الحالية\n"
    "/help - عرض قائمة الأوامر المتاحة"
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

    elif text == 'ارسل رسالة لصاحب البوت':
        await update.message.reply_text(
            REQUEST_OWNER_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(
                MAIN_MENU_KEYBOARD, resize_keyboard=True, one_time_keyboard=True
            )
        )
        return SEND_MESSAGE_TO_OWNER

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
                MESSAGE_SENT_CONFIRMATION,
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

# Handler for sending message to bot owner
async def send_message_to_owner_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        return await start(update, context)

    if text:
        try:
            message_to_owner = f"📩 رسالة من @{username} (ID: {user_id}):\n\n{text}"
            await context.bot.send_message(chat_id=SPECIAL_USER_ID, text=message_to_owner)
            await update.message.reply_text(
                MESSAGE_SENT_CONFIRMATION,
                reply_markup=ReplyKeyboardMarkup(
                    REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
                )
            )
            logger.info(f"Forwarded message from @{username} (ID: {user_id}) to SPECIAL_USER_ID {SPECIAL_USER_ID}.")
        except Exception as e:
            logger.error(f"Failed to send message to SPECIAL_USER_ID {SPECIAL_USER_ID}: {e}")
            await update.message.reply_text(MESSAGE_SEND_FAILURE)
    else:
        await update.message.reply_text("الرجاء إرسال رسالة صالحة أو العودة للقائمة الرئيسية.")

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

async def setup_application(application):
    # Delete any existing webhook to avoid conflicts with getUpdates
    try:
        await application.bot.delete_webhook()
        logger.info("تم حذف أي webhooks موجودة بنجاح.")
    except Exception as e:
        logger.error(f"فشل في حذف webhook الموجود: {e}")

async def main():
    # Retrieve the bot token from environment variables
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("متغير البيئة BOT_TOKEN غير مضبوط.")
        exit(1)

    # Initialize the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Define the main ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_OPTION: [
                MessageHandler(
                    filters.Regex('^(حساب غياب النظري|حساب غياب العملي|ارسل رسالة لصاحب البوت)$'), choice_handler
                )
            ],
            GET_THEORETICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, theoretical_credit)
            ],
            GET_PRACTICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, practical_credit)
            ],
            SEND_MESSAGE_TO_OWNER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_to_owner_handler)
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

    # Setup application (e.g., delete existing webhooks)
    await setup_application(application)

    # Start the bot
    logger.info("البوت يبدأ العمل...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
