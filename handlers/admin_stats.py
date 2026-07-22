from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import SessionLocal, User

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار ربات (فقط برای ادمین)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ شما دسترسی به این دستور را ندارید.")
        return
    
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        users_with_test = db.query(User).filter(User.has_used_test == True).count()
        users_with_subscription = db.query(User).filter(User.vpn_username != None).count()
        
        stats_text = (
            "📊 <b>داشبورد مدیریتی ربات</b>\n\n"
            f"👥 <b>کل کاربران ثبت‌نام شده:</b> {total_users} نفر\n"
            f"🎁 <b>کاربران استفاده‌کننده از تست:</b> {users_with_test} نفر\n"
            f"💎 <b>کاربران دارای اشتراک فعال:</b> {users_with_subscription} نفر\n\n"
            "🟢 ربات در حال حاضر فعال و پایدار است."
        )
        
        await update.message.reply_text(stats_text, parse_mode="HTML")
    finally:
        db.close()
