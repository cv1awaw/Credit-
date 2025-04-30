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
BROADCAST_ASK_MESSAGE, BROADCAST_CONFIRMATION = range(20, 22)
USER_M_WAITING_FOR_MESSAGE = 30
HEY_WAITING_FOR_MESSAGE = 999

# IDs
SPECIAL_USER_ID = 77655677655
AUTHORIZED_USER_ID = 6177929931

# JSON files
MUTED_USERS_FILE = 'muted_users.json'
USERS_FILE = 'users.json'
WELCOME_MSGS_FILE = 'welcome_msgs.json'

MAIN_MENU_KEYBOARD = [
    ['حساب غياب النظري', 'حساب غياب العملي'],
    ['ارسل رسالة لصاحب البوت', 'حساب درجتك بلبلوك']
]

def load_override_welcomes():
    if os.path.exists(WELCOME_MSGS_FILE):
        with open(WELCOME_MSGS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
            except json.JSONDecodeError:
                return {}
    return {}

def save_override_welcomes(mapping):
    with open(WELCOME_MSGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in mapping.items()}, f, ensure_ascii=False)

def load_muted_users():
    if os.path.exists(MUTED_USERS_FILE):
        with open(MUTED_USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_muted_users(muted):
    with open(MUTED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(muted), f)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError):
                return {}
    return {}

def save_users(users_dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in users_dict.items()}, f)

muted_users = load_muted_users()
known_users = load_users()
override_welcome_messages = load_override_welcomes()

def log_user_activity(user_id):
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
    user = update.effective_user
    user_id = user.id

    log_user_activity(user_id)
    logger.info(f"User {user.username or user_id} used /start - Message: {update.message.text}")

    if user_id in muted_users:
        await update.message.reply_text("⚠️ لقد تم كتمك من استخدام هذا البوت.")
        return ConversationHandler.END

    if user_id in override_welcome_messages:
        welcome_text = override_welcome_messages[user_id]
    elif user_id == SPECIAL_USER_ID:
        welcome_text = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^"
    else:
        welcome_text = (
            "السلام عليكم \n"
            "البوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
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
    
    logger.info(f"User {user.username or user.id} selected: {text}")

    if text == 'حساب غياب النظري':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة النظري (مثال: 3.0).\n\n"
            "أو اختر 'العودة للقائمة الرئيسية':",
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
        )
        return GET_THEORETICAL_CREDIT

    elif text == 'حساب غياب العملي':
        await update.message.reply_text(
            "اكتب رقم الكردت لمادة العملي (مثال: 1.5).\n\n"
            "أو اختر 'العودة للقائمة الرئيسية':",
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
        )
        return GET_PRACTICAL_CREDIT

    elif text == 'ارسل رسالة لصاحب البوت':
        await update.message.reply_text(
            "يمكنك إرسال رسالتك الآن، أو اختر 'العودة للقائمة الرئيسية':",
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
        )
        return SEND_MESSAGE

    elif text == 'حساب درجتك بلبلوك':
        await update.message.reply_text(
            "شكد المادة عليها بلبلوك؟ (اكتب رقم فقط)\n\n"
            "أو اختر 'العودة للقائمة الرئيسية':",
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
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
    
    logger.info(f"User {user.username or user.id} entered theoretical: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.2352941176
        await update.message.reply_text(f"غيابك للنظري هو: {result:.2f}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return GET_THEORETICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

async def practical_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} entered practical: {text}")

    if text == 'العودة للقائمة الرئيسية':
        await show_main_menu(update, context)
        return CHOOSING_OPTION

    try:
        credit = float(text)
        result = credit * 8 * 0.1176470588
        await update.message.reply_text(f"غيابك للعملي هو: {result:.2f}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return GET_PRACTICAL_CREDIT

    await show_main_menu(update, context)
    return CHOOSING_OPTION

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
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
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
            reply_markup=ReplyKeyboardMarkup([['العودة للقائمة الرئيسية']], True, True)
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
        await update.message.reply_text(f"درجتك بلبلوك هي: {result:.2f}")
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return BLOK_TAKEN

    await show_main_menu(update, context)
    return CHOOSING_OPTION

async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    log_user_activity(user.id)
    text = (update.message.text or "").strip()
    
    logger.info(f"User {user.username or user.id} sent message: {text}")

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

# —————— أوامر المشرف الإضافية ——————

async def hey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ أنت غير مصرح لك.")
        return ConversationHandler.END
    args = context.args
    if not args:
        await update.message.reply_text("استخدام: /hey <user_id>")
        return ConversationHandler.END
    try:
        target = int(args[0])
    except ValueError:
        await update.message.reply_text("الرجاء إدخال معرف مستخدم صالح.")
        return ConversationHandler.END
    context.user_data['hey_target'] = target
    await update.message.reply_text("أرسل الترحيب المخصص:")
    return HEY_WAITING_FOR_MESSAGE

async def hey_message_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    target = context.user_data.get('hey_target')
    override_welcome_messages[target] = update.message.text or ""
    save_override_welcomes(override_welcome_messages)
    await update.message.reply_text(f"✔ تم تعيين الترحيب للمستخدم {target}.")
    return ConversationHandler.END

async def user_m_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ أنت غير مصرح لك.")
        return ConversationHandler.END
    args = context.args
    if not args:
        await update.message.reply_text("استخدام: /user_m <user_id>")
        return ConversationHandler.END
    try:
        target = int(args[0])
    except ValueError:
        await update.message.reply_text("الرجاء إدخال معرف مستخدم صالح.")
        return ConversationHandler.END
    context.user_data['user_m_target'] = target
    await update.message.reply_text(f"أرسل الرسالة للمستخدم {target}:")
    return USER_M_WAITING_FOR_MESSAGE

async def user_m_message_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    target = context.user_data.get('user_m_target')
    text = update.message.text or ""
    if text:
        try:
            await context.bot.send_message(chat_id=target, text=text)
            await update.message.reply_text(f"✔ تم إرسال الرسالة إلى {target}.")
        except Exception as e:
            logger.error(e)
            await update.message.reply_text("❌ حدث خطأ أثناء الإرسال.")
    else:
        await update.message.reply_text("❌ لا توجد رسالة.")
    return ConversationHandler.END

async def broadcast_ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ أنت غير مصرح لك.")
        return ConversationHandler.END
    await update.message.reply_text("أرسل محتوى البث:")
    return BROADCAST_ASK_MESSAGE

async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['broadcast_message'] = update.message.text or ""
    await update.message.reply_text("تأكيد الإرسال إلى الجميع؟ (نعم/لا)")
    return BROADCAST_CONFIRMATION

async def broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    resp = (update.message.text or "").strip().lower()
    if resp in ['نعم', 'yes', 'y']:
        msg = context.user_data.get('broadcast_message', '')
        count = 0
        for uid in known_users.keys():
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
                count += 1
            except:
                pass
        await update.message.reply_text(f"✔ تم الإرسال إلى {count} مستخدمين.")
    else:
        await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

async def active_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    total_users = len(known_users)
    now = datetime.now()
    daily_active = sum(
        1 for t in known_users.values()
        if (now - datetime.fromisoformat(t)) < timedelta(hours=24)
    )
    await update.message.reply_text(
        f"📊 إحصائيات البوت:\n\n"
        f"• إجمالي المستخدمين: {total_users}\n"
        f"• المستخدمين النشطين اليوم: {daily_active}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == AUTHORIZED_USER_ID:
        admin_help_text = (
            "🚀 أوامر المشرف:\n\n"
            "/help - إظهار هذه القائمة\n"
            "/active - إظهار إحصائيات الاستخدام\n"
            "/muteid <userid> - كتم مستخدم\n"
            "/unmuteid <userid> - إلغاء كتم\n"
            "/mutelist - عرض المكتومين\n"
            "/user_m <userid> - إرسال رسالة لمستخدم\n"
            "/hey <userid> - تعيين ترحيب مخصص\n"
            "/hey_r <userid> - حذف ترحيب مخصص\n"
            "/new - بث رسالة للجميع\n"
            "/cancel - إلغاء العملية"
        )
        await update.message.reply_text(admin_help_text)
    else:
        user_help_text = (
            "مرحباً! أنا بوت للمساعدة.\n"
            "الأوامر المتاحة:\n"
            "/start - بدء المحادثة\n"
            "/help - عرض المساعدة"
        )
        await update.message.reply_text(user_help_text)

async def mutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    if not muted_users:
        await update.message.reply_text("لا يوجد مستخدمون مكتومون.")
    else:
        await update.message.reply_text("Muted users:\n" + "\n".join(map(str, muted_users)))

async def muteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("استخدام: /muteid <id>")
        return
    try:
        uid = int(args[0])
        muted_users.add(uid)
        save_muted_users(muted_users)
        await update.message.reply_text(f"✔ تم كتم {uid}.")
    except:
        await update.message.reply_text("❌ خطأ.")

async def unmuteid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("استخدام: /unmuteid <id>")
        return
    try:
        uid = int(args[0])
        muted_users.discard(uid)
        save_muted_users(muted_users)
        await update.message.reply_text(f"✔ تم إلغاء كتم {uid}.")
    except:
        await update.message.reply_text("❌ خطأ.")

async def hey_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("استخدام: /hey_r <id>")
        return
    try:
        uid = int(args[0])
        override_welcome_messages.pop(uid, None)
        save_override_welcomes(override_welcome_messages)
        await update.message.reply_text(f"✔ تم حذف الترحيب للمستخدم {uid}.")
    except:
        await update.message.reply_text("❌ خطأ.")

class MuteFilter(MessageFilter):
    def filter(self, message):
        return message.from_user and (message.from_user.id in muted_users)

async def handle_muted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    note = (
        f"⚠️ Attempt by muted user:\n"
        f"• ID: {user.id}\n"
        f"• Username: @{user.username or 'N/A'}"
    )
    try:
        await context.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=note)
    except:
        pass
    await update.message.reply_text("⚠️ أنت مكتوم ولا يمكنك استخدام البوت.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("لم أفهم رسالتك، استخدم الأزرار أو اكتب /start")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception occurred:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("حدث خطأ غير متوقع. يرجى المحاولة لاحقًا.")

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .build()

    # إضافة handler للمستخدمين المكتومين
    mute_filter = MuteFilter()
    app.add_handler(MessageHandler(mute_filter, handle_muted), group=0)

    # Conversation handler الرئيسي
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
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
        ],
        allow_reentry=True
    )
    app.add_handler(conv_handler)

    # Conversation handler لـ /hey
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('hey', hey_command)],
        states={
            HEY_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, hey_message_received)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # Conversation handler لـ /user_m
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('user_m', user_m_command)],
        states={
            USER_M_WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, user_m_message_received)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # Conversation handler للبث /new
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('new', broadcast_ask_command)],
        states={
            BROADCAST_ASK_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirm)
            ],
            BROADCAST_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_execute)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # أوامر المشرف الأساسية
    app.add_handler(CommandHandler('active', active_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('mutelist', mutelist_command))
    app.add_handler(CommandHandler('muteid', muteid_command))
    app.add_handler(CommandHandler('unmuteid', unmuteid_command))
    app.add_handler(CommandHandler('hey_r', hey_remove_command))

    # Fallback handler
    app.add_handler(MessageHandler(filters.ALL, default_handler))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("Starting bot...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
