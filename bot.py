from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.request import HTTPXRequest
from config import BOT_TOKEN, SUPPORT_ID
from handlers.start import start, reply_keyboard_handler, check_membership_handler
from handlers.buy import (
    show_volume_plans, select_volume, enter_custom_volume, enter_sub_name, send_receipt, 
    receive_receipt, cancel_buy, SELECTING_VOLUME, ENTERING_CUSTOM_VOLUME, ENTERING_SUB_NAME,
    WAITING_FOR_PAYMENT, WAITING_FOR_RECEIPT
)
from handlers.admin import (
    confirm_payment, final_confirm_payment, reject_payment, 
    final_reject_payment, cancel_confirm
)
from handlers.user import (
    get_sub_link_handler, renew_subscription_handler, support_handler,
    show_my_subscriptions, give_free_test, show_single_subscription_details, back_to_subs_handler
)
from handlers.admin_stats import stats_command

PROXY_URL = "socks5://127.0.0.1:10808"

async def support_reply(update, context):
    keyboard = [[InlineKeyboardButton("📩 ارسال پیام به پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")]]
    await update.message.reply_text("🛠️ <b>برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

def main():
    print("✅ ربات با ساختار ماژولار روشن شد...")
    request = HTTPXRequest(proxy=PROXY_URL)
    app = Application.builder().token(BOT_TOKEN).request(request).get_updates_request(request).build()

    buy_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_volume_plans, pattern="^start_buy$"),
            MessageHandler(filters.Regex("^🛒 خرید اشتراک$"), show_volume_plans)
        ],
        states={
            SELECTING_VOLUME: [CallbackQueryHandler(select_volume, pattern="^vol_")],
            ENTERING_CUSTOM_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_volume)],
            ENTERING_SUB_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_sub_name)],
            WAITING_FOR_PAYMENT: [CallbackQueryHandler(send_receipt, pattern="^send_receipt$")],
            WAITING_FOR_RECEIPT: [MessageHandler(filters.TEXT | filters.PHOTO, receive_receipt)],
        },
        fallbacks=[CallbackQueryHandler(cancel_buy, pattern="^cancel_buy$")],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(buy_handler)
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.Regex("^📊 اشتراک‌های من$"), show_my_subscriptions))
    app.add_handler(MessageHandler(filters.Regex("^🎁 تست رایگان$"), give_free_test))
    app.add_handler(MessageHandler(filters.Regex("^📞 پشتیبانی$"), support_reply))
    
    app.add_handler(CallbackQueryHandler(check_membership_handler, pattern="^check_membership$"))
    app.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(final_confirm_payment, pattern="^final_confirm_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(reject_payment, pattern="^reject_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(final_reject_payment, pattern="^final_reject_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(cancel_confirm, pattern="^cancel_confirm$"))
    app.add_handler(CallbackQueryHandler(show_single_subscription_details, pattern="^sub_detail_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(back_to_subs_handler, pattern="^back_to_subs$"))
    app.add_handler(CallbackQueryHandler(get_sub_link_handler, pattern="^get_sub_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(renew_subscription_handler, pattern="^renew_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(support_handler, pattern="^support$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler))

    print("🟢 ربات آماده است. /start را بزنید.")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد.")
