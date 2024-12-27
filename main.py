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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Set to DEBUG for more verbose output
)
logger = logging.getLogger(__name__)

# Define states for ConversationHandler
CHOOSING_OPTION, GET_THEORETICAL_CREDIT, GET_PRACTICAL_CREDIT, SEND_MESSAGE = range(4)

# Define additional states for /user_id command
USER_ID_WAITING_FOR_MESSAGE = 4

# Special User IDs
SPECIAL_USER_ID = 77655677655  # User to receive messages from /user_id command
AUTHORIZED_USER_ID = 6177929931  # User authorized to use /user_id and mute commands

# Path to the muted users file
MUTED_USERS_FILE = 'muted_users.json'

# Keyboard layout
REPLY_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت']
]

# Utility functions to manage muted users
def load_muted_users():
    if os.path.exists(MUTED_USERS_FILE):
        with open(MUTED_USERS_FILE, 'r') as file:
            try:
                return set(json.load(file))
            except json.JSONDecodeError:
                return set()
    return set()

def save_muted_users(muted_users):
    with open(MUTED_USERS_FILE, 'w') as file:
        json.dump(list(muted_users), file)

# Initialize muted users set
muted_users = load_muted_users()

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    # Check if user is muted
    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    # Log the user ID for debugging
    logger.info(f"User {user.username or 'No Username'} with ID {user_id} started the bot.")

    if user_id == SPECIAL_USER_ID:
        # Personalized welcome message for the special user
        welcome_message = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
        logger.info(f"Sending personalized message to user ID {user_id}.")
    else:
        # Default welcome message for other users
        welcome_message = (
            "السلام عليكم \nالبوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
            "اذا بقى يشكل عندك البوت اضغط /start"
        )
        logger.info(f"Sending default message to user ID {user_id}.")

    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardMarkup(
            REPLY_KEYBOARD, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOOSING_OPTION

# Handler for choosing an option from the main menu
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
            "ارسل ركدت العملي",
            reply_markup=ReplyKeyboardMarkup(
                [['العودة للقائمة الرئيسية']], resize_keyboard=True, one_time_keyboard=True
            )
        )
        return GET_PRACTICAL_CREDIT

    elif text == 'ارسل رسالة لصاحب البوت':
        await update.message.reply_text(
            "يرجى إرسال رسالتك الآن.",
            reply_markup=ReplyKeyboardRemove()
        )
        return SEND_MESSAGE

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
        return await start(update, context)

    try:
        credit = float(text)
        result = credit * 8 * 0.23
        await update.message.reply_text(f"{result}")
        return await start(update, context)
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية.")
        return GET_THEORETICAL_CREDIT

# Handler for practical credit input
async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'العودة للقائمة الرئيسية':
        return await start(update, context)

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        await update.message.reply_text(f"{result}")
        return await start(update, context)
    except ValueError:
        await update.message.reply_text("الرجاء إرسال رقم صحيح أو العودة للقائمة الرئيسية.")
        return GET_PRACTICAL_CREDIT

# /user_id command — only for AUTHORIZED_USER_ID
async def user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id

    logger.info(f"User {user.username or 'No Username'} with ID {user_id} invoked /user_id command.")

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Please send your message.",
        reply_markup=ReplyKeyboardRemove()
    )
    return USER_ID_WAITING_FOR_MESSAGE

# Handler for processing the user's message in /user_id conversation
async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or "No Username"

    if text:
        try:
            formatted_message = f"Message from @{username} (ID: {user_id}):\n\n{text}"
            await context.bot.send_message(chat_id=SPECIAL_USER_ID, text=formatted_message)
            await update.message.reply_text("رسالتك تم إرسالها بنجاح.")
            logger.info(f"Message from user ID {user_id} sent to SPECIAL_USER_ID {SPECIAL_USER_ID}.")
        except Exception as e:
            logger.error(f"Failed to send message to SPECIAL_USER_ID {SPECIAL_USER_ID}: {e}")
            await update.message.reply_text("لم يتم إرسال الرسالة. يرجى المحاولة لاحقًا.")
    else:
        await update.message.reply_text("لم يتم إرسال الرسالة. يرجى توفير نص صالح.")

    return ConversationHandler.END

# Handler for sending messages to the bot owner
async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    username = user.username or "No Username"

    if text:
        try:
            formatted_message = f"رسالة من @{username} (ID: {user_id}):\n\n{text}"
            await context.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=formatted_message)
            await update.message.reply_text("تم إرسال رسالتك بنجاح.")
            logger.info(f"Forwarded message from @{username} (ID: {user_id}) to AUTHORIZED_USER_ID {AUTHORIZED_USER_ID}.")
        except Exception as e:
            logger.error(f"Failed to forward message to AUTHORIZED_USER_ID {AUTHORIZED_USER_ID}: {e}")
            await update.message.reply_text("لم يتم إرسال الرسالة. يرجى المحاولة لاحقًا.")
    else:
        await update.message.reply_text("لم يتم إرسال الرسالة. يرجى توفير نص صالح.")

    return ConversationHandler.END

# /muteid command — only for AUTHORIZED_USER_ID
async def muteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /muteid <userid>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if target_id in muted_users:
        await update.message.reply_text(f"User ID {target_id} is already muted.")
    else:
        muted_users.add(target_id)
        save_muted_users(muted_users)
        await update.message.reply_text(f"User ID {target_id} has been muted.")
        logger.info(f"User ID {target_id} has been muted by {user_id}.")

# /unmuteid command — only for AUTHORIZED_USER_ID
async def unmuteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /unmuteid <userid>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if target_id in muted_users:
        muted_users.remove(target_id)
        save_muted_users(muted_users)
        await update.message.reply_text(f"User ID {target_id} has been unmuted.")
        logger.info(f"User ID {target_id} has been unmuted by {user_id}.")
    else:
        await update.message.reply_text(f"User ID {target_id} is not muted.")

# /mutelist command — only for AUTHORIZED_USER_ID
async def mutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if muted_users:
        muted_list = "\n".join(str(uid) for uid in muted_users)
        await update.message.reply_text(f"Muted User IDs:\n{muted_list}")
    else:
        await update.message.reply_text("No users are currently muted.")

# Fallback handler for /user_id conversation
async def user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "تم إلغاء العملية. للبدء من جديد، ارسل /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Fallback handler for main conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "تم إلغاء العملية. للبدء من جديد، ارسل /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Default handler for unknown or out-of-context messages
async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    # Check if user is muted
    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return

    # Instead of re-sending the full welcome message, send a brief prompt:
    await update.message.reply_text(
        "عذراً، لم أفهم ذلك. الرجاء استخدام الأزرار أو اكتب /start لإعادة التشغيل."
    )

# Error handler to catch and log all errors
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("An unexpected error occurred. Please try again later.")

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
                    filters.Regex('^(حساب غياب النظري|حساب غياب العملي|ارسل رسالة لصاحب البوت)$'), 
                    choice_handler
                )
            ],
            GET_THEORETICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, theoretical_credit)
            ],
            GET_PRACTICAL_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, practical_credit)
            ],
            SEND_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_handler)
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

    # Handle any other messages that don't fit into the above handlers
    general_handler = MessageHandler(filters.ALL & ~filters.COMMAND, default_handler)

    # Add handlers to the application
    application.add_handler(conv_handler)
    application.add_handler(user_id_conv_handler)
    application.add_handler(CommandHandler('muteid', muteid_command))
    application.add_handler(CommandHandler('unmuteid', unmuteid_command))
    application.add_handler(CommandHandler('mutelist', mutelist_command))
    application.add_handler(general_handler)  # This should be added last

    # Add the error handler
    application.add_error_handler(error_handler)

    # Start the bot with polling and drop any pending updates
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
