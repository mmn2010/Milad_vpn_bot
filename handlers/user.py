from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from vpn_panel import create_user_in_panel, get_user_info_from_panel
from database import SessionLocal, User, Subscription
from helpers import require_membership
from config import SUPPORT_ID

async def show_my_subscriptions(update, context):
    if not await require_membership(update, context):
        return
    
    telegram_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user or not user.subscriptions or len(user.subscriptions) == 0:
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text("⚠️ شما هنوز هیچ اشتراکی ندارید.")
        else:
            await update.message.reply_text("⚠️ شما هنوز هیچ اشتراکی ندارید.")
        db.close()
        return
        
    keyboard = []
    for sub in user.subscriptions:
        display_name = sub.name if sub.name else sub.volume_name
        keyboard.append([InlineKeyboardButton(f"📦 {display_name}", callback_data=f"sub_detail_{sub.id}")])
    
    text = f"📊 شما <b>{len(user.subscriptions)}</b> اشتراک دارید.\nلطفا برای مشاهده جزئیات، روی اشتراک مورد نظر کلیک کنید:"
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    db.close()

async def show_single_subscription_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_id = int(query.data.replace("sub_detail_", ""))
    db = SessionLocal()
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    
    if not sub:
        await query.edit_message_text("⚠️ اشتراک یافت نشد.")
        db.close()
        return
        
    await query.edit_message_text("⏳ در حال دریافت اطلاعات...")
    result = await get_user_info_from_panel(sub.vpn_username)
    
    if result["success"]:
        data = result["data"]
        used_bytes = data.get("used_traffic", 0) or 0
        total_bytes = data.get("data_limit", 0) or 0
        remaining_bytes = total_bytes - used_bytes
        remaining_mb = round(remaining_bytes / (1024 * 1024), 2)
        
        expire_str = data.get("expire")
        if expire_str:
            try:
                expire_date = datetime.fromisoformat(expire_str.replace("Z", "+00:00"))
                days_left = (expire_date - datetime.now(expire_date.tzinfo)).days
            except:
                days_left = "نامشخص"
        else:
            days_left = "نامحدود"
            
        status = "✅ فعال" if data.get("status") == "active" else "❌ غیرفعال"
        
        response_text = (
            f"━━━━━━━━━━━━━━━\n"
            f"📊 <b>جزئیات: {sub.name}</b>\n\n"
            f"👤 نام کاربری: <code>{sub.vpn_username}</code>\n"
            f"💾 حجم کل: {sub.volume_name}\n"
            f"📌 وضعیت: {status}\n"
            f"💾 حجم باقی‌مانده: {remaining_mb} مگابایت\n"
            f"⏰ روزهای باقی‌مانده: {days_left}\n"
            f"━━━━━━━━━━━━━━━"
        )
        
        sub_keyboard = [
            [InlineKeyboardButton("🔗 دریافت لینک اتصال", callback_data=f"get_sub_{sub.id}")],
            [InlineKeyboardButton("🔄 تمدید اشتراک", callback_data=f"renew_{sub.id}")],
            [InlineKeyboardButton("🔙 بازگشت به لیست اشتراک‌ها", callback_data="back_to_subs")]
        ]
        
        await query.edit_message_text(
            response_text, 
            reply_markup=InlineKeyboardMarkup(sub_keyboard),
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text(f"❌ خطا در دریافت اطلاعات:\n<code>{result['error']}</code>", parse_mode="HTML")
    db.close()

async def back_to_subs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user or not user.subscriptions or len(user.subscriptions) == 0:
        await query.edit_message_text("⚠️ شما هنوز هیچ اشتراکی ندارید.")
        db.close()
        return
        
    keyboard = []
    for sub in user.subscriptions:
        display_name = sub.name if sub.name else sub.volume_name
        keyboard.append([InlineKeyboardButton(f"📦 {display_name}", callback_data=f"sub_detail_{sub.id}")])
    
    await query.edit_message_text(
        f"📊 شما <b>{len(user.subscriptions)}</b> اشتراک دارید.\nلطفا برای مشاهده جزئیات، روی اشتراک مورد نظر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    db.close()

async def give_free_test(update, context):
    if not await require_membership(update, context):
        return
    telegram_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user and user.has_used_test:
        await update.message.reply_text("⚠️ شما قبلا از تست رایگان خود استفاده کرده‌اید.")
        db.close()
        return
    await update.message.reply_text("⏳ در حال ساخت تست رایگان...")
    result = await create_user_in_panel(is_test=True)
    if result["success"]:
        if not user:
            user = User(telegram_id=telegram_id, username=update.effective_user.username)
            db.add(user)
            db.commit()
        user.has_used_test = True
        new_sub = Subscription(
            user_id=user.id,
            name="🎁 تست رایگان",
            vpn_username=result['username'],
            volume_name="100 مگابایت",
            volume_bytes=104857600,
            expire_date=datetime.now() + timedelta(hours=24),
            is_test=True
        )
        db.add(new_sub)
        db.commit()
        db.close()
        sub_link = result['data'].get("sub_link") or result['data'].get("subscription_url") or result['data'].get("url")
        response_text = f"✅ <b>تست رایگان شما آماده است!</b>\n\n👤 نام کاربری: <code>{result['username']}</code>\n🔗 <b>لینک اشتراک تست:</b>\n<code>{sub_link}</code>\n\n⚠️ این اشتراک محدود به 100 مگابایت و 24 ساعت است."
        await update.message.reply_text(response_text, parse_mode="HTML")
    else:
        db.close()
        await update.message.reply_text(f"❌ خطا:\n<code>{result['error']}</code>", parse_mode="HTML")

async def get_sub_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_id = int(query.data.replace("get_sub_", ""))
    db = SessionLocal()
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        await query.edit_message_text("⚠️ اشتراک یافت نشد.")
        db.close()
        return
    result = await get_user_info_from_panel(sub.vpn_username)
    if result["success"]:
        sub_link = result["data"].get("sub_url") or result["data"].get("subscription_url")
        if sub_link:
            # اینجا هم پیام را ویرایش می‌کنیم تا چت شلوغ نشود، اما دکمه بازگشت را اضافه می‌کنیم
            back_keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=f"sub_detail_{sub.id}")]]
            await query.edit_message_text(
                f"🔗 <b>لینک اشتراک:</b>\n<code>{sub_link}</code>\n\n<i>این لینک را کپی کرده و در برنامه VPN خود وارد کنید.</i>", 
                reply_markup=InlineKeyboardMarkup(back_keyboard),
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text("⚠️ لینک یافت نشد.")
    db.close()

async def renew_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_id = int(query.data.replace("renew_", ""))
    back_keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=f"sub_detail_{sub.id}")]]
    await query.edit_message_text(
        f"🚧 بخش تمدید اشتراک #{sub_id} به زودی فعال می‌شود!",
        reply_markup=InlineKeyboardMarkup(back_keyboard)
    )

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("📩 ارسال پیام به پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")]]
    await query.edit_message_text(
        "🛠️ <b>پشتیبانی</b>\n\nبرای رفع مشکلات یا راهنمایی، لطفا روی دکمه زیر کلیک کنید تا مستقیما به پی‌وی پشتیبانی منتقل شوید:", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode="HTML"
    )
