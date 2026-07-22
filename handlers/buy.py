from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from helpers import require_membership, VOLUME_PLANS, PRICE_PER_GB, SUBSCRIPTION_DAYS, format_price, calculate_custom_price, gb_to_bytes
from config import CARD_NUMBER, CARD_OWNER_NAME

SELECTING_VOLUME, ENTERING_CUSTOM_VOLUME, ENTERING_SUB_NAME, WAITING_FOR_PAYMENT, WAITING_FOR_RECEIPT = range(5)

async def show_volume_plans(update, context):
    if not await require_membership(update, context):
        return ConversationHandler.END
    keyboard = []
    for plan_id, plan_info in VOLUME_PLANS.items():
        price_text = format_price(plan_info["price"])
        keyboard.append([InlineKeyboardButton(f"💾 {plan_info['name']} - {price_text}", callback_data=f"vol_{plan_id}")])
    keyboard.append([InlineKeyboardButton(f"🎯 حجم دلخواه (هر گیگ {format_price(PRICE_PER_GB)})", callback_data="vol_custom")])
    keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")])
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text("🛒 <b>خرید اشتراک یک ماهه</b>\n\nلطفا حجم مورد نظر خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text("🛒 <b>خرید اشتراک یک ماهه</b>\n\nلطفا حجم مورد نظر خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return SELECTING_VOLUME

async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await show_volume_plans(update, context)

async def select_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    volume_plan_id = query.data.replace("vol_", "")
    if volume_plan_id == "custom":
        await query.message.reply_text("🎯 <b>حجم دلخواه</b>\n\nلطفا حجم مورد نظر خود را <b>به گیگابایت</b> وارد کنید.\n(فقط عدد وارد کنید، مثلا: 75)", parse_mode="HTML")
        return ENTERING_CUSTOM_VOLUME
    plan_info = VOLUME_PLANS[volume_plan_id]
    context.user_data["volume_bytes"] = plan_info["bytes"]
    context.user_data["volume_name"] = plan_info["name"]
    context.user_data["price"] = plan_info["price"]
    await query.message.reply_text("🏷️ <b>نام‌گذاری اشتراک</b>\n\nلطفا یک نام برای این اشتراک انتخاب کنید (مثلا: اکانت گوشی، اکانت لپ‌تاپ).\n<i>این نام فقط در ربات نمایش داده می‌شود و تاثیری در پنل ندارد.</i>", parse_mode="HTML")
    return ENTERING_SUB_NAME

async def enter_custom_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    try:
        gb = int(user_input)
        if gb <= 0:
            await update.message.reply_text("⚠️ لطفا یک عدد مثبت وارد کنید.")
            return ENTERING_CUSTOM_VOLUME
        price = calculate_custom_price(gb)
        volume_bytes = gb_to_bytes(gb)
        context.user_data["volume_bytes"] = volume_bytes
        context.user_data["volume_name"] = f"{gb} گیگابایت"
        context.user_data["price"] = price
        await update.message.reply_text("🏷️ <b>نام‌گذاری اشتراک</b>\n\nلطفا یک نام برای این اشتراک انتخاب کنید (مثلا: اکانت گوشی، اکانت لپ‌تاپ).\n<i>این نام فقط در ربات نمایش داده می‌شود.</i>", parse_mode="HTML")
        return ENTERING_SUB_NAME
    except ValueError:
        await update.message.reply_text("⚠️ لطفا فقط عدد وارد کنید (مثلا: 75)")
        return ENTERING_CUSTOM_VOLUME

async def enter_sub_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_name = update.message.text.strip()
    context.user_data["sub_name"] = sub_name
    price = context.user_data["price"]
    volume_name = context.user_data["volume_name"]
    payment_text = f"🧾 <b>فاکتور نهایی</b>\n\n💾 حجم اینترنت: {volume_name}\n📅 مدت اشتراک: 1 ماه ({SUBSCRIPTION_DAYS} روز)\n━━━━━━━━━━━━━━━\n💰 <b>مبلغ قابل پرداخت: {format_price(price)}</b>\n\n💳 <b>اطلاعات کارت:</b>\n👤 به نام: <b>{CARD_OWNER_NAME}</b>\n🔢 شماره کارت:\n<code>{CARD_NUMBER}</code>\n\n📝 لطفا مبلغ را واریز و <b>رسید پرداخت</b> را ارسال نمایید."
    keyboard = [[InlineKeyboardButton("✅ ارسال رسید پرداخت", callback_data="send_receipt")], [InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]]
    await update.message.reply_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return WAITING_FOR_PAYMENT

async def send_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📸 لطفا <b>عکس رسید پرداخت</b> یا <b>شماره پیگیری</b> را ارسال کنید.\n\n⏳ پس از بررسی توسط ادمین، اشتراک شما فعال خواهد شد.", parse_mode="HTML")
    return WAITING_FOR_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import ADMIN_ID
    user = update.effective_user
    user_data = context.user_data
    order_info = {"user_id": user.id, "username": user.username or user.first_name, "volume": user_data.get("volume_name"), "price": user_data.get("price"), "volume_bytes": user_data.get("volume_bytes"), "sub_name": user_data.get("sub_name")}
    admin_text = f"🔔 <b>سفارش جدید!</b>\n\n👤 کاربر: @{order_info['username']} (ID: {user.id})\n💾 حجم: {order_info['volume']}\n🏷️ نام انتخابی: {order_info['sub_name']}\n💰 مبلغ: {format_price(order_info['price'])}\n\n📝 رسید پرداخت در پیام بعدی ارسال شده است."
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"رسید پرداخت از کاربر {user.id}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید و فعال‌سازی", callback_data=f"confirm_{user.id}")], [InlineKeyboardButton("❌ رد", callback_data=f"reject_{user.id}")]]))
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"رسید پرداخت (متنی): {update.message.text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید و فعال‌سازی", callback_data=f"confirm_{user.id}")], [InlineKeyboardButton("❌ رد", callback_data=f"reject_{user.id}")]]))
    context.bot_data[f"order_{user.id}"] = {"volume_bytes": user_data.get("volume_bytes"), "volume_name": user_data.get("volume_name"), "price": user_data.get("price"), "sub_name": user_data.get("sub_name")}
    await update.message.reply_text("✅ <b>رسید شما دریافت شد!</b>\n\n⏳ لطفا منتظر بمانید تا ادمین پرداخت را بررسی و اشتراک شما را فعال کند.", parse_mode="HTML")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text("❌ خرید لغو شد.")
    return ConversationHandler.END
