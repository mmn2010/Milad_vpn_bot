from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from vpn_panel import create_user_in_panel
from database import SessionLocal, User, Subscription
from helpers import SUBSCRIPTION_DAYS
from config import ADMIN_ID, SUPPORT_ID
from datetime import datetime, timedelta

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⚠️ فقط ادمین می‌تواند تأیید کند.")
        return
    user_id = int(query.data.replace("confirm_", ""))
    await query.message.reply_text(f"⚠️ <b>آیا مطمئن هستید؟</b>\n\nدر حال تأیید پرداخت کاربر با آیدی <code>{user_id}</code>...\nاین عمل قابل بازگشت نیست.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ بله، مطمئنم - فعال کن", callback_data=f"final_confirm_{user_id}")], [InlineKeyboardButton("❌ نه، منصرف شدم", callback_data="cancel_confirm")]]), parse_mode="HTML")

async def final_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⚠️ فقط ادمین می‌تواند تأیید کند.")
        return
    user_id = int(query.data.replace("final_confirm_", ""))
    order = context.bot_data.get(f"order_{user_id}")
    if not order:
        await query.message.reply_text("❌ اطلاعات سفارش یافت نشد.")
        return
    result = await create_user_in_panel(is_test=False, volume_bytes=order["volume_bytes"], days=SUBSCRIPTION_DAYS)
    if result["success"]:
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(telegram_id=user_id)
            db.add(user)
            db.commit()
        new_sub = Subscription(
            user_id=user.id,
            name=f"📦 {order.get('sub_name', order['volume_name'])}",
            vpn_username=result['username'],
            volume_name=order['volume_name'],
            volume_bytes=order['volume_bytes'],
            expire_date=datetime.now() + timedelta(days=SUBSCRIPTION_DAYS),
            is_test=False
        )
        db.add(new_sub)
        db.commit()
        db.close()
        sub_link = result['data'].get("sub_link") or result['data'].get("subscription_url") or result['data'].get("url")
        await context.bot.send_message(chat_id=user_id, text=f"✅ <b>پرداخت شما تأیید شد!</b>\n\n👤 نام کاربری: <code>{result['username']}</code>\n💾 حجم: {order['volume_name']}\n🔗 <b>لینک اشتراک شما:</b>\n<code>{sub_link}</code>\n\n🎉 از خرید شما متشکریم!", parse_mode="HTML")
        await query.edit_message_text(text=f"✅ <b>پرداخت تأیید و اشتراک فعال شد.</b>\n\n👤 کاربر: <code>{user_id}</code>\n💾 حجم: {order['volume_name']}", parse_mode="HTML")
        del context.bot_data[f"order_{user_id}"]
    else:
        await query.message.reply_text(f"❌ خطا در ساخت اشتراک:\n{result['error']}")

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⚠️ فقط ادمین می‌تواند رد کند.")
        return
    user_id = int(query.data.replace("reject_", ""))
    await query.message.reply_text(f"⚠️ <b>آیا مطمئن هستید؟</b>\n\nدر حال رد پرداخت کاربر با آیدی <code>{user_id}</code>...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ بله، مطمئنم - رد کن", callback_data=f"final_reject_{user_id}")], [InlineKeyboardButton("❌ نه، منصرف شدم", callback_data="cancel_confirm")]]), parse_mode="HTML")

async def final_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⚠️ فقط ادمین می‌تواند رد کند.")
        return
    user_id = int(query.data.replace("final_reject_", ""))
    await context.bot.send_message(chat_id=user_id, text=f"❌ <b>پرداخت شما رد شد.</b>\n\nلطفا با پشتیبانی تماس بگیرید:\n@{SUPPORT_ID}", parse_mode="HTML")
    await query.edit_message_text(text=f"❌ <b>پرداخت رد شد.</b>\n\n👤 کاربر: <code>{user_id}</code>", parse_mode="HTML")
    if f"order_{user_id}" in context.bot_data:
        del context.bot_data[f"order_{user_id}"]

async def cancel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ عملیات لغو شد.")
