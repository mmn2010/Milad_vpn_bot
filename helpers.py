from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from config import CHANNEL_ID

# ==========================================
# تنظیمات پلن‌های حجمی (همه یک ماهه)
# ==========================================

VOLUME_PLANS = {
    "10gb": {"name": "۱۰ گیگابایت", "bytes": 10 * 1024 * 1024 * 1024, "price": 50000},
    "25gb": {"name": "۲۵ گیگابایت", "bytes": 25 * 1024 * 1024 * 1024, "price": 100000},
    "50gb": {"name": "۵۰ گیگابایت", "bytes": 50 * 1024 * 1024 * 1024, "price": 180000},
    "100gb": {"name": "۱۰۰ گیگابایت", "bytes": 100 * 1024 * 1024 * 1024, "price": 320000},
    "200gb": {"name": "۲۰۰ گیگابایت", "bytes": 200 * 1024 * 1024 * 1024, "price": 600000},
}

PRICE_PER_GB = 4500
SUBSCRIPTION_DAYS = 30

# ==========================================
# توابع کمکی
# ==========================================

def format_price(price: int) -> str:
    """تبدیل قیمت به فرمت خوانا"""
    return f"{price:,} تومان"

def calculate_custom_price(gb: int) -> int:
    """محاسبه قیمت برای حجم دلخواه"""
    return gb * PRICE_PER_GB

def gb_to_bytes(gb: int) -> int:
    """تبدیل گیگابایت به بایت"""
    return gb * 1024 * 1024 * 1024

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی عضویت کاربر در کانال"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

async def require_membership(update, context, callback=None):
    """بررسی عضویت و نمایش پیام در صورت عدم عضویت"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.from_user.id
    
    if not await check_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton("✅ بررسی مجدد عضویت", callback_data="check_membership")]
        ]
        
        if callback:
            await callback.message.reply_text(
                "⚠️ <b>عضویت اجباری</b>\n\n"
                "برای استفاده از این بخش، لطفاً ابتدا در کانال ما عضو شوید.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "⚠️ <b>عضویت اجباری</b>\n\n"
                "برای استفاده از ربات، لطفاً ابتدا در کانال ما عضو شوید.\n\n"
                f"📢 کانال: {CHANNEL_ID}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        return False
    return True