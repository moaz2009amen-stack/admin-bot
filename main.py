"""
البوت الإداري الذكي
====================
متوافق مع python-telegram-bot==21.3 + OpenAI
"""

import os
import logging
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

if not TOKEN:
    raise ValueError("❌ مفيش TOKEN")
if not OPENAI_KEY:
    raise ValueError("❌ مفيش OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

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
            InlineKeyboardButton("📊 إحصائيات", callback_data="إحصائيات"),
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
    رسالة = (
        "👋 *أهلاً! أنا بوتك الإداري الذكي*\n\n"
        "أقدر أساعدك في:\n"
        "🔹 حظر وكتم الأعضاء المخالفين\n"
        "🔹 إصدار تحذيرات تلقائية\n"
        "🔹 مسح الرسائل المزعجة\n"
        "🔹 الرد على الأسئلة بالذكاء الاصطناعي\n\n"
        "⚡ *أوامر الإدارة — رد على رسالة العضو واكتب:*\n"
        "حظر | فك حظر | كتم | فك كتم | تحذير | مسح\n\n"
        "🤖 *للذكاء الاصطناعي:*\n"
        "اذكرني في الجروب أو اسألني في الخاص\n\n"
        "اختار من القائمة 👇"
    )
    await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


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
            "🤖 *الذكاء الاصطناعي:*\n"
            "اذكرني @اسم_البوت أو اسألني في الخاص"
        ),
        "إحصائيات": "📊 *إحصائيات الجروب*\n\n🚧 ستكون متاحة في المرحلة الثانية",
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

    # ==================== أوامر الإدارة العربية ====================
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

    # ==================== الذكاء الاصطناعي ====================
    في_الخاص = update.effective_chat.type == "private"
    اتذكر = اسم_البوت.lower() in نص_الرسالة.lower()

    if في_الخاص or اتذكر:
        سؤال = نص_الرسالة.replace(اسم_البوت, "").strip()
        if not سؤال:
            await update.message.reply_text("نعم؟ 😊 كيف أساعدك؟")
            return

        try:
            await context.bot.send_chat_action(update.effective_chat.id, "typing")
            رد = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1000,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "أنت مساعد ذكي في مجموعة تليجرام. "
                            "ردودك دائماً بالعربية، مختصرة ومفيدة. "
                            "لو سُئلت عن معلومة، أجب بدقة. "
                            "لا تستخدم ماركداون معقد."
                        )
                    },
                    {"role": "user", "content": سؤال}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as خطأ:
            await update.message.reply_text(f"❌ حصل خطأ: {خطأ}")


def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))

    print("✅ البوت شغال...")
    تطبيق.run_polling()


if __name__ == "__main__":
    main()
