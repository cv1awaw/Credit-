import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Define states for ConversationHandler
CHOOSING, TYPING_CREDIT = range(2)

# Keyboard options
keyboard_main = [['نظرية', 'عملية']]
keyboard_back = [['رجوع']]

reply_markup_main = ReplyKeyboardMarkup(
    keyboard_main, one_time_keyboard=True, resize_keyboard=True
)

reply_markup_back = ReplyKeyboardMarkup(
    keyboard_back, one_time_keyboard=True, resize_keyboard=True
)

# Bot Token
BOT_TOKEN = "MY BOT TOKEN"  # Replace with your actual bot token or use environment variables

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message and show main keyboard."""
    await update.message.reply_text(
        "السلام عليكم تم انشاء البوت بواسطة @iwanna2die لمساعدة الطلاب في حساب الكردت",
        reply_markup=reply_markup_main,
    )
    return CHOOSING

async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's choice between Theory and Practical."""
    choice = update.message.text
    if choice == 'نظرية':  # Theory
        await update.message.reply_text(
            "ارسل كردت المادة",
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data['mode'] = 'theory'
        return TYPING_CREDIT
    elif choice == 'عملية':  # Practical
        await update.message.reply_text(
            "ارسل كردت المادة",
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data['mode'] = 'practical'
        return TYPING_CREDIT
    else:
        # If user sends something else, resend the welcome message
        await update.message.reply_text(
            "السلام عليكم تم انشاء البوت بواسطة @iwanna2die لمساعدة الطلاب في حساب الكردت",
            reply_markup=reply_markup_main,
        )
        return CHOOSING

async def received_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the credit number and send calculation."""
    credit_text = update.message.text
    try:
        credit = float(credit_text)
    except ValueError:
        await update.message.reply_text(
            "الرجاء ارسال رقم صحيح للكردت.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return TYPING_CREDIT

    mode = context.user_data.get('mode')

    if mode == 'theory':
        number = credit * 8 * 0.23
    elif mode == 'practical':
        number = credit * 8 * 0.1176470588
    else:
        # If mode is not set, restart the conversation
        await update.message.reply_text(
            "حدث خطأ. يرجى المحاولة مرة أخرى.",
            reply_markup=reply_markup_main,
        )
        return CHOOSING

    # Send the final number
    await update.message.reply_text(
        f"{number}",
        reply_markup=reply_markup_back,
    )
    return CHOOSING

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the Back button to return to main menu."""
    await update.message.reply_text(
        "اختر نوع الحساب:",
        reply_markup=reply_markup_main,
    )
    return CHOOSING

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unknown messages."""
    await update.message.reply_text(
        "السلام عليكم تم انشاء البوت بواسطة @iwanna2die لمساعدة الطلاب في حساب الكردت",
        reply_markup=reply_markup_main,
    )
    return CHOOSING

def main():
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex('^(نظرية|عملية)$'), choosing)
            ],
            TYPING_CREDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_credit)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^رجوع$'), back_to_main),
            MessageHandler(filters.COMMAND, unknown),
            MessageHandler(filters.ALL, unknown),
        ],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ALL, unknown))

    # Run the bot until you press Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
