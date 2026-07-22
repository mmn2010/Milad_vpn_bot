print("=" * 50)
print("تست helpers.py")
print("=" * 50)

# تست 1: import helpers
try:
    import helpers
    print("✅ helpers.py با موفقیت import شد")
except Exception as e:
    print(f"❌ خطا در import helpers: {e}")
    exit()

# تست 2: بررسی توابع
try:
    print(f"✅ VOLUME_PLANS: {len(helpers.VOLUME_PLANS)} پلن")
    print(f"✅ PRICE_PER_GB: {helpers.PRICE_PER_GB}")
    print(f"✅ format_price(50000): {helpers.format_price(50000)}")
    print(f"✅ gb_to_bytes(1): {helpers.gb_to_bytes(1)}")
    print(f"✅ calculate_custom_price(5): {helpers.calculate_custom_price(5)}")
except Exception as e:
    print(f"❌ خطا در توابع helpers: {e}")

# تست 3: import handlers
print("\n" + "=" * 50)
print("تست handlers")
print("=" * 50)

try:
    from handlers import start, buy, admin, user
    print("✅ همه handler ها با موفقیت import شدند")
except Exception as e:
    print(f"❌ خطا در import handlers: {e}")

# تست 4: بررسی bot.py
print("\n" + "=" * 50)
print("تست bot.py")
print("=" * 50)

try:
    import bot
    print("✅ bot.py با موفقیت import شد")
except Exception as e:
    print(f"❌ خطا در import bot.py: {e}")

print("\n" + "=" * 50)
print("تست کامل شد!")
print("=" * 50)