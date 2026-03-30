"""
البوت الإداري الذكي - المرحلة الأولى
=====================================
المتطلبات:
    pip install python-telegram-bot==20.7
    
الإعداد:
    1. روح @BotFather على تليجرام
    2. اعمل بوت جديد واخد الـ TOKEN
    3. حط الـ TOKEN في المتغير TOKEN أدناه
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================== الإعدادات ====================
TOKEN = "ضع_التوكن_هنا"  # ← غير ده بالتوكن بتاعك

# ==================== اللوج ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==================== القائمة الرئيسية ====================
def القائمة_الرئيسية():
    """بترجع أزرار القائمة الرئيسية"""
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


# ==================== /start ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب عند أول استخدام"""
    رسالة_ترحيب = (
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
    await update.message.reply_text(
        رسالة_ترحيب,
        parse_mode="Markdown",
        reply_markup=القائمة_الرئيسية()
    )


# ==================== /مساعدة ====================
async def مساعدة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شرح تفصيلي لكل الأوامر"""
    نص = (
        "📖 *دليل الاستخدام الكامل*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔨 *حظر عضو*\n"
        "رد على رسالة العضو واضغط حظر، أو استخدم:\n"
        "`/ban` — بعد الرد على رسالته\n\n"
        "🔓 *فك الحظر*\n"
        "اكتب ID العضو وافك حظره\n\n"
        "🔇 *كتم عضو*\n"
        "رد على رسالته واختار كتم\n\n"
        "⚠️ *التحذيرات*\n"
        "بعد 3 تحذيرات → حظر تلقائي\n\n"
        "🗑 *مسح رسالة*\n"
        "رد على الرسالة واضغط مسح\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 *ملاحظة:* لازم البوت يكون أدمن في الجروب"
    )
    await update.message.reply_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


# ==================== معالج الأزرار ====================
async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بيتعامل مع كل ضغطة زرار"""
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    if بيانات == "مساعدة":
        نص = (
            "📖 *دليل الاستخدام*\n\n"
            "🔨 *حظر* — رد على رسالة العضو ثم اضغط حظر\n"
            "🔓 *فك الحظر* — أرسل ID العضو\n"
            "🔇 *كتم* — رد على رسالة العضو ثم اضغط كتم\n"
            "⚠️ *تحذير* — 3 تحذيرات = حظر تلقائي\n"
            "🗑 *مسح* — رد على الرسالة وامسحها\n\n"
            "💡 البوت لازم يكون أدمن في الجروب"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "إحصائيات":
        # في المرحلة الجاية هنربطها بقاعدة بيانات
        نص = (
            "📊 *إحصائيات الجروب*\n\n"
            "🚧 هذه الخاصية ستكون متاحة في المرحلة الثانية\n"
            "وهتشمل: عدد المحظورين، التحذيرات، الرسائل المحذوفة"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "حظر":
        نص = (
            "🔨 *حظر عضو*\n\n"
            "الطريقة:\n"
            "1️⃣ ارجع للجروب\n"
            "2️⃣ رد على رسالة العضو\n"
            "3️⃣ اكتب `/ban`"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "كتم":
        نص = (
            "🔇 *كتم عضو*\n\n"
            "الطريقة:\n"
            "1️⃣ ارجع للجروب\n"
            "2️⃣ رد على رسالة العضو\n"
            "3️⃣ اكتب `/mute`"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "فك_حظر":
        نص = (
            "🔓 *فك الحظر*\n\n"
            "الطريقة:\n"
            "اكتب `/unban [ID العضو]`\n\n"
            "مثال: `/unban 123456789`"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "فك_كتم":
        نص = (
            "🔊 *فك الكتم*\n\n"
            "الطريقة:\n"
            "1️⃣ رد على رسالة العضو\n"
            "2️⃣ اكتب `/unmute`"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "تحذير":
        نص = (
            "⚠️ *التحذيرات*\n\n"
            "الطريقة:\n"
            "1️⃣ رد على رسالة العضو\n"
            "2️⃣ اكتب `/warn`\n\n"
            "📌 بعد 3 تحذيرات → حظر تلقائي"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())

    elif بيانات == "مسح":
        نص = (
            "🗑 *مسح رسالة*\n\n"
            "الطريقة:\n"
            "1️⃣ رد على الرسالة المراد مسحها\n"
            "2️⃣ اكتب `/del`"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


# ==================== أوامر الإدارة ====================
async def حظر_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ban — حظر العضو اللي رددت على رسالته"""
    # التحقق إن المستخدم أدمن
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return

    # التحقق إن في رسالة مردود عليها
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
    """/unban [ID] — فك حظر عضو"""
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return

    if not context.args:
        await update.message.reply_text("📝 اكتب: `/unban [ID العضو]`", parse_mode="Markdown")
        return

    try:
        id_عضو = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, id_عضو)
        await update.message.reply_text(f"🔓 تم فك الحظر عن العضو بنجاح.")
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل فك الحظر: {خطأ}")


async def كتم_عضو(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/mute — كتم العضو اللي رددت على رسالته"""
    from telegram import ChatPermissions

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
    """/unmute — فك كتم العضو اللي رددت على رسالته"""
    from telegram import ChatPermissions

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
                can_send_media_messages=True,
                can_send_other_messages=True,
            )
        )
        await update.message.reply_text(f"🔊 تم فك كتم {عضو.first_name} بنجاح.")
    except Exception as خطأ:
        await update.message.reply_text(f"❌ فشل فك الكتم: {خطأ}")


async def مسح_رسالة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/del — مسح الرسالة اللي رددت عليها"""
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
    """/warn — تحذير العضو (بعد 3 تحذيرات = حظر تلقائي)"""
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ رد على رسالة العضو اللي تريد تحذيره.")
        return

    عضو = update.message.reply_to_message.from_user

    # نظام التحذيرات (مؤقتاً في الذاكرة — هنربطه بقاعدة بيانات في المرحلة الثانية)
    if "تحذيرات" not in context.bot_data:
        context.bot_data["تحذيرات"] = {}

    مفتاح = f"{update.effective_chat.id}_{عضو.id}"
    context.bot_data["تحذيرات"][مفتاح] = context.bot_data["تحذيرات"].get(مفتاح, 0) + 1
    عدد = context.bot_data["تحذيرات"][مفتاح]

    if عدد >= 3:
        # حظر تلقائي بعد 3 تحذيرات
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
            context.bot_data["تحذيرات"][مفتاح] = 0
            await update.message.reply_text(
                f"🚫 تم حظر {عضو.first_name} تلقائياً بعد 3 تحذيرات!"
            )
        except Exception as خطأ:
            await update.message.reply_text(f"❌ فشل الحظر التلقائي: {خطأ}")
    else:
        await update.message.reply_text(
            f"⚠️ تحذير {عدد}/3 لـ {عضو.first_name}\n"
            f"{'تحذيران متبقيان' if عدد == 1 else 'تحذير متبقي'} قبل الحظر التلقائي."
        )


# ==================== دالة مساعدة ====================
async def هو_ادمن(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بتتحقق إن المستخدم أدمن في الجروب"""
    مستخدم = update.effective_user
    شات = update.effective_chat

    # في الشات الخاص، كل حاجة مسموحة
    if شات.type == "private":
        return True

    عضو_الشات = await context.bot.get_chat_member(شات.id, مستخدم.id)
    return عضو_الشات.status in ["administrator", "creator"]


# ==================== تشغيل البوت ====================
def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    # أوامر المساعدة
    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("help", مساعدة))

    # أوامر الإدارة
    تطبيق.add_handler(CommandHandler("ban", حظر_عضو))
    تطبيق.add_handler(CommandHandler("unban", فك_حظر_عضو))
    تطبيق.add_handler(CommandHandler("mute", كتم_عضو))
    تطبيق.add_handler(CommandHandler("unmute", فك_كتم_عضو))
    تطبيق.add_handler(CommandHandler("del", مسح_رسالة))
    تطبيق.add_handler(CommandHandler("warn", تحذير_عضو))

    # معالج الأزرار
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))

    print("✅ البوت شغال...")
    تطبيق.run_polling()


if __name__ == "__main__":
    main()
