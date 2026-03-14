"""
البوت الإداري الذكي - النسخة المتقدمة
========================================
متوافق مع python-telegram-bot==21.3 + Groq
"""

import os
import logging
from datetime import time
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TOKEN")
GROQ_KEY = os.environ.get("GROQ_KEY")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

if not TOKEN:
    raise ValueError("❌ مفيش TOKEN")
if not GROQ_KEY:
    raise ValueError("❌ مفيش GROQ_KEY")

groq_client = Groq(api_key=GROQ_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

قوانين_الجروب = """
📋 *قوانين الجروب*

1️⃣ الاحترام المتبادل بين الأعضاء
2️⃣ ممنوع السب والشتيمة
3️⃣ ممنوع الإعلانات والسبام
4️⃣ ممنوع نشر روابط بدون إذن
5️⃣ الالتزام بموضوع الجروب

⚠️ مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي.

نتمنى لك وقتاً ممتعاً! 🎉
"""
رسائل_مجدولة = [
    {
        "الوقت": time(6, 0),
        "الرسالة": "🌅 *صباح الخير!*\n\nاللهم بارك لنا في يومنا ووفقنا للمذاكرة والتحصيل 📚\n\n💡 *تذكر:* كل دقيقة تذاكر فيها دلوقتي هي خطوة نحو نجاحك غداً ⭐"
    },
    {
        "الوقت": time(11, 0),
        "الرسالة": "🌙 *مساء الخير!*\n\nاللهم اجعل ما تعلمناه اليوم نافعاً وثبته في قلوبنا 🤲\n\n📖 *لا تنسَ:* مراجعة ما درسته اليوم قبل النوم تثبت المعلومة في ذهنك 💪"
    },
    {
        "الوقت": time(18, 0),
        "الرسالة": "☀️ *تذكير وقت الظهر!*\n\nاللهم أعنّا على ذكرك وشكرك وحسن عبادتك 🤲\n\n📚 *وقت المذاكرة الذهبي!* الفترة دي من أفضل الأوقات للتركيز، استغلها 💡"
    },
]

def القائمة_الرئيسية():
    أزرار = [
        [
            InlineKeyboardButton("🔨 حظر عضو", callback_data="حظر"),
            InlineKeyboardButton("🔓 فك الحظر", callback_data="فك_حظر"),
        ],
        [
            InlineKeyboardButton("🔇 كتم عضو", callback_data="كتم"),
            InlineKeyboardButton("🔊 فك الكتم", callback_data="فك_كتم"),
        ],
        [
            InlineKeyboardButton("⚠️ تحذير", callback_data="تحذير"),
            InlineKeyboardButton("🗑 مسح رسالة", callback_data="مسح"),
        ],
        [
            InlineKeyboardButton("📋 القوانين", callback_data="قوانين"),
            InlineKeyboardButton("❓ المساعدة", callback_data="مساعدة"),
        ],
    ]
    return InlineKeyboardMarkup(أزرار)


async def هو_ادمن(update, context):
    مستخدم = update.effective_user
    شات = update.effective_chat
    if شات.type == "private":
        return True
    عضو_الشات = await context.bot.get_chat_member(شات.id, مستخدم.id)
    return عضو_الشات.status in ["administrator", "creator"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user

    # إشعار للأونر كل ما حد يبدأ محادثة
    if OWNER_ID != 0 and مستخدم.id != OWNER_ID:
        يوزر = f"@{مستخدم.username}" if مستخدم.username else "مفيش يوزرنيم"
        إشعار = (
            f"🆕 *مستخدم جديد بدأ محادثة!*\n\n"
            f"👤 الاسم: {مستخدم.first_name}\n"
            f"🔗 اليوزر: {يوزر}\n"
            f"🆔 الـ ID: `{مستخدم.id}`"
        )
        try:
            await context.bot.send_message(OWNER_ID, إشعار, parse_mode="Markdown")
        except:
            pass

    رسالة = (
        "👋 *أهلاً! أنا بووووو — بوتك الإداري الذكي*\n\n"
        "أقدر أساعدك في:\n"
        "🔹 حظر وكتم الأعضاء المخالفين\n"
        "🔹 الترحيب بالأعضاء الجدد تلقائياً\n"
        "🔹 الرد على الأسئلة بالذكاء الاصطناعي\n"
        "🔹 إرسال رسائل مجدولة\n\n"
        "⚡ *أوامر الإدارة — رد على رسالة العضو واكتب:*\n"
        "حظر | فك حظر | كتم | فك كتم | تحذير | مسح\n\n"
        "اختار من القائمة 👇"
    )
    await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    نتيجة = update.chat_member
    عضو_جديد = نتيجة.new_chat_member.user
    شات = update.effective_chat

    if نتيجة.new_chat_member.status == "member":
        رسالة_ترحيب = (
            f"👋 *أهلاً وسهلاً {عضو_جديد.first_name}!*\n\n"
            f"يسعدنا انضمامك لـ *{شات.title}* 🎉\n\n"
            f"{قوانين_الجروب}"
        )
        await context.bot.send_message(شات.id, رسالة_ترحيب, parse_mode="Markdown")


async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    نصوص = {
        "مساعدة": (
            "📖 *دليل الاستخدام*\n\n"
            "رد على رسالة العضو واكتب:\n"
            "🔨 *حظر* — لحظر العضو\n"
            "🔓 *فك حظر* — لفك الحظر\n"
            "🔇 *كتم* — لكتم العضو\n"
            "🔊 *فك كتم* — لفك الكتم\n"
            "⚠️ *تحذير* — 3 تحذيرات = حظر تلقائي\n"
            "🗑 *مسح* — لمسح الرسالة\n\n"
            "📋 *القوانين* — اكتب 'القوانين' في الجروب"
        ),
        "قوانين": قوانين_الجروب,
        "حظر": "🔨 *حظر عضو*\n\nرد على رسالة العضو واكتب:\n*حظر*",
        "فك_حظر": "🔓 *فك الحظر*\n\nرد على رسالة العضو واكتب:\n*فك حظر*",
        "كتم": "🔇 *كتم عضو*\n\nرد على رسالة العضو واكتب:\n*كتم*",
        "فك_كتم": "🔊 *فك الكتم*\n\nرد على رسالة العضو واكتب:\n*فك كتم*",
        "تحذير": "⚠️ *التحذيرات*\n\nرد على رسالة العضو واكتب:\n*تحذير*\n\n📌 بعد 3 تحذيرات → حظر تلقائي",
        "مسح": "🗑 *مسح رسالة*\n\nرد على الرسالة واكتب:\n*مسح*",
    }

    نص = نصوص.get(بيانات, "❓ أمر غير معروف")
    await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def معالج_الرسائل(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    نص_الرسالة = update.message.text.strip()
    الرسالة_المردود_عليها = update.message.reply_to_message
    بوت_info = await context.bot.get_me()
    اسم_البوت = f"@{بوت_info.username}"
    في_الخاص = update.effective_chat.type == "private"

    if الرسالة_المردود_عليها and await هو_ادمن(update, context):
        عضو = الرسالة_المردود_عليها.from_user

        if نص_الرسالة == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔨 تم حظر {عضو.first_name} بنجاح.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ فشل الحظر: {خطأ}")
            return

        elif نص_الرسالة == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {عضو.first_name} بنجاح.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ فشل فك الحظر: {خطأ}")
            return

        elif نص_الرسالة == "كتم":
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id,
                    عضو.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
                await update.message.reply_text(f"🔇 تم كتم {عضو.first_name} بنجاح.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ فشل الكتم: {خطأ}")
            return

        elif نص_الرسالة == "فك كتم":
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id,
                    عضو.id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=False,
                    )
                )
                await update.message.reply_text(f"🔊 تم فك كتم {عضو.first_name} بنجاح.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ فشل فك الكتم: {خطأ}")
            return

        elif نص_الرسالة == "مسح":
            try:
                await الرسالة_المردود_عليها.delete()
                await update.message.delete()
            except Exception as خطأ:
                await update.message.reply_text(f"❌ فشل المسح: {خطأ}")
            return

        elif نص_الرسالة == "تحذير":
            if "تحذيرات" not in context.bot_data:
                context.bot_data["تحذيرات"] = {}
            مفتاح = f"{update.effective_chat.id}_{عضو.id}"
            context.bot_data["تحذيرات"][مفتاح] = context.bot_data["تحذيرات"].get(مفتاح, 0) + 1
            عدد = context.bot_data["تحذيرات"][مفتاح]
            if عدد >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                    context.bot_data["تحذيرات"][مفتاح] = 0
                    await update.message.reply_text(f"🚫 تم حظر {عضو.first_name} تلقائياً بعد 3 تحذيرات!")
                except Exception as خطأ:
                    await update.message.reply_text(f"❌ فشل الحظر التلقائي: {خطأ}")
            else:
                متبقي = 3 - عدد
                await update.message.reply_text(
                    f"⚠️ تحذير {عدد}/3 لـ {عضو.first_name}\n"
                    f"{'تحذيران' if متبقي == 2 else 'تحذير'} متبقي قبل الحظر التلقائي."
                )
            return

    if نص_الرسالة in ["القوانين", "قوانين", "الرولز", "rules"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return

    اتذكر = اسم_البوت.lower() in نص_الرسالة.lower()
    فيه_سؤال = "؟" in نص_الرسالة or "?" in نص_الرسالة

    if في_الخاص or اتذكر or فيه_سؤال:
        سؤال = نص_الرسالة.replace(اسم_البوت, "").strip()
        if not سؤال:
            return
        try:
            await context.bot.send_chat_action(update.effective_chat.id, "typing")
            رد = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "أنت مساعد ذكي في مجموعة تليجرام. "
                            "ردودك دائماً بالعربية، مختصرة ومفيدة. "
                            "لا تستخدم ماركداون معقد."
                        )
                    },
                    {"role": "user", "content": سؤال}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as خطأ:
            await update.message.reply_text(f"❌ حصل خطأ: {خطأ}")


async def إرسال_رسالة_مجدولة(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0:
        return
    رسالة = context.job.data
    await context.bot.send_message(CHAT_ID, رسالة, parse_mode="Markdown")


def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))

    if CHAT_ID != 0:
        for رسالة_مجدولة in رسائل_مجدولة:
            تطبيق.job_queue.run_daily(
                إرسال_رسالة_مجدولة,
                time=رسالة_مجدولة["الوقت"],
                data=رسالة_مجدولة["الرسالة"],
            )

    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
