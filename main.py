import logging
from datetime import time
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, filters,
)
from config import TOKEN
from handlers import (
    start, ctrl, prompt_command, help_command, setup_commands,
    ترحيب_عضو_جديد, معالج_الأزرار, معالج_الملفات, معالج_الرسائل,
    تقرير_يومي
)
from telegram import Update

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    if not TOKEN:
        raise ValueError("مفيش TOKEN في الـ environment variables!")

    تطبيق = ApplicationBuilder().token(TOKEN).post_init(setup_commands).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("ctrl", ctrl))
    تطبيق.add_handler(CommandHandler("prompt", prompt_command))
    تطبيق.add_handler(CommandHandler("help", help_command))
    تطبيق.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.Document.ALL, معالج_الملفات))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))

    # تقرير يومي الساعة 8 صباحاً بتوقيت القاهرة
    تطبيق.job_queue.run_daily(تقرير_يومي, time=time(5, 0))

    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
