import sys
import traceback

print("🔄 جاري تشغيل البوت...")

try:
    import logging
    from datetime import time
    from telegram.ext import (
        ApplicationBuilder, CommandHandler, CallbackQueryHandler,
        MessageHandler, ChatMemberHandler, filters,
    )
    from telegram import Update
    print("✅ telegram imported")

    from config import TOKEN
    print(f"✅ config imported | TOKEN: {'موجود' if TOKEN else 'مش موجود'}")

    from database import supabase
    print(f"✅ database imported | supabase: {'موجود' if supabase else 'مش موجود'}")

    from ai import اسأل_ai
    print("✅ ai imported")

    from camp import جيب_بيانات_جروب, قراءة_أسئلة, ابدأ_معسكر, إرسال_سؤال, نهاية_المعسكر, جيب_ترتيب
    print("✅ camp imported")

    from handlers import (
        start, ctrl, prompt_command, help_command, setup_commands,
        ترحيب_عضو_جديد, معالج_الأزرار, معالج_الملفات, معالج_الرسائل,
        تقرير_يومي
    )
    print("✅ handlers imported")

except Exception as e:
    print(f"❌ Import Error: {e}")
    traceback.print_exc()
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    if not TOKEN:
        print("❌ مفيش TOKEN!")
        sys.exit(1)

    print("🔄 جاري بناء التطبيق...")
    تطبيق = ApplicationBuilder().token(TOKEN).post_init(setup_commands).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("ctrl", ctrl))
    تطبيق.add_handler(CommandHandler("prompt", prompt_command))
    تطبيق.add_handler(CommandHandler("help", help_command))
    تطبيق.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.Document.ALL, معالج_الملفات))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))

    تطبيق.job_queue.run_daily(تقرير_يومي, time=time(5, 0))

    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
