from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from helpers import require_membership, check_membership
from config import SUPPORT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_membership(update, context):
        return ConversationHandler.END
    reply_keyboard = ReplyKeyboardMarkup([[KeyboardButton("🛒 خرید اشتراک"), KeyboardButton("📊 اشتراک‌های من")], [KeyboardButton("🎁 تست رایگان"), KeyboardButton("📞 پشتیبانی")]], resize_keyboard=True, one_time_keyboard=False)
    welcome_text = "👋 <b>سلام! به ربات فروش VPN خوش آمدید.</b>\n\n🚀 اینترنت سریع و پایدار را تجربه کنید.\nمی‌توانید قبل از خرید، یک تست رایگان ۱۰۰ مگابایتی دریافت کنید!\n\nاز دکمه‌های زیر استفاده کنید:"
    await update.message.reply_text(welcome_text, reply_markup=reply_keyboard, parse_mode="HTML")

async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.buy import show_volume_plans
    from handlers.user import show_my_subscriptions, give_free_test
    text = update.message.text
    if text == "🛒 خرید اشتراک":
        return await show_volume_plans(update, context)
    elif text == "📊 اشتراک‌های من":
        await show_my_subscriptions(update, context)
    elif text == "🎁 تست رایگان":
        await give_free_test(update, context)
    elif text == "📞 پشتیبانی":
        keyboard = [[InlineKeyboardButton("📩 ارسال پیام به پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")]]
        await update.message.reply_text("🛠️ برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_membership_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_membership(query.from_user.id, context):
        await query.message.reply_text("✅ عضویت شما تأیید شد!\n/start را بزنید.")
    else:
        await query.message.reply_text("❌ شما هنوز عضو کانال نیستید.")
