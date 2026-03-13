"""
البوت الإداري الذكي
====================
متوافق مع python-telegram-bot==21.3
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("❌ مفيش TOKEN — ضيفه في Environment Variables على Railway")

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
        "🔹 إحصائيات الجروب\n\n"
        "⚡ *طريقة الاستخدام:*\n"
        "1️⃣ أضفني للجروب أو القناة\n"
        "2️⃣ اعمل للبوت صلاحية أدمن\n"
        "3️⃣ اختار الأمر اللي تريده من القائمة 👇"
    )
    await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def مساعدة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    نص = (
        "📖 *دليل الاستخدام الكامل*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔨 *حظر عضو* — رد على رسالته واكتب `/ban`\n\n"
        "🔓 *فك الحظر* — اكتب `/unban [ID]`\n\n"
        "🔇 *كتم عضو* — رد على رسالته واكتب `/mute`\n\n"
        "🔊 *فك الكتم* — رد على رسالته واكتب `/unmute`\n\n"
        "⚠️ *تحذير* — رد على رسالته واكتب `/warn`\n"
        "📌 بعد 3 تحذيرات = حظر تلقائي\n\n"
        "🗑 *مسح رسالة* — رد عليها واكتب `/del`\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 *ملاحظة:* لازم البوت يكون أدمن في الجروب"
    )
    await update.message.reply_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    نصوص = {
        "مساعدة": (
            "📖 *دليل الاستخدام*\n\n"
            "🔨 *حظر* — رد على رسالة العضو ثم اكتب `/ban`\n"
            "🔓 *فك الحظر* — اكتب `/unban [ID]`\n"
            "🔇 *كتم* — رد على رسالة العضو ثم اكتب `/mute`\n"
            "⚠️ *تحذير* — 3 تحذيرات = حظر تلقائي\n"
            "🗑 *مسح* — رد على الرسالة واكتب `/del`\n\n"
            "💡 البوت لازم يكون أدمن في الجروب"
        ),
        "إحصائيات": (
            "📊 *إحصائيات الجروب*\n\n"
            "🚧 هذه الخاصية ستكون متاحة في المرحلة الثانية\n"
            "وهتشمل: عدد المحظورين، التحذيرات، الرسائل المحذوفة"
        ),
        "حظر": "🔨 *حظر عضو*\n\n1️⃣ ارجع للجروب\n2️⃣ رد على رسالة العضو\n3️⃣ اكتب `/ban`",
        "فك_حظر": "🔓 *فك الحظر*\n\nاكتب `/unban [ID العضو]`\n\nمثال: `/unban 123456789`",
        "كتم": "🔇 *كتم عضو*\n\n1️⃣ ارجع للجروب\n2️⃣ رد على رسالة العضو\n3️⃣ اكتب `/mute`",
        "فك_كتم": "🔊 *فك الكتم*\n\n1️⃣ رد على رسالة العضو\n2️⃣ اكتب `/unmute`",
        "تحذير": "⚠️ *التحذيرات*\n\n1️⃣ رد على رسالة العضو\n2️⃣ اكتب `/warn`\n\n📌 بعد 3 تحذيرات → حظر تلقائي",
        "مسح": "🗑 *مسح رسالة*\n\n1️⃣ رد على الرسالة المراد مسحها\n2️⃣ اكتب `/del`",
    }

    نص = نصوص.get(بيانات, "❓ أمر غير معروف")
    await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def حظر_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على رسالة العضو اللي تريد حظره.")
        return
    عضو = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
        await update.message.reply_text(f"🔨 تم حظر {عضو.first_name} بنجاح.")
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل الحظر: {خطأ}")


async def فك_حظر_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not context.args:
        await update.message.reply_text("📝 اكتب: `/unban [ID العضو]`", parse_mode="Markdown")
        return
    try:
        id_عضو = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, id_عضو)
        await update.message.reply_text("🔓 تم فك الحظر بنجاح.")
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل فك الحظر: {خطأ}")


async def كتم_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على رسالة العضو اللي تريد كتمه.")
        return
    عضو = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            عضو.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 تم كتم {عضو.first_name} بنجاح.")
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل الكتم: {خطأ}")


async def فك_كتم_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على رسالة العضو اللي تريد فك كتمه.")
        return
    عضو = update.message.reply_to_message.from_user
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


async def مسح_رسالة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على الرسالة اللي تريد مسحها.")
        return
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل المسح: {خطأ}")


async def تحذير_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على رسالة العضو اللي تريد تحذيره.")
        return

    عضو = update.message.reply_to_message.from_user

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


def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("help", مساعدة))
    تطبيق.add_handler(CommandHandler("ban", حظر_عضو))
    تطبيق.add_handler(CommandHandler("unban", فك_حظر_عضو))
    تطبيق.add_handler(CommandHandler("mute", كتم_عضو))
    تطبيق.add_handler(CommandHandler("unmute", فك_كتم_عضو))
    تطبيق.add_handler(CommandHandler("del", مسح_رسالة))
    تطبيق.add_handler(CommandHandler("warn", تحذير_عضو))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))

    print("✅ البوت شغال...")
    تطبيق.run_polling()


if __name__ == "__main__":
    main()
