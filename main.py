"""
البوت الإداري الذكي - النسخة المتقدمة
========================================
متوافق مع python-telegram-bot==21.3 + Groq
"""

import os
import re
import io
import logging
import random
from datetime import time, datetime
from groq import Groq
import openpyxl
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

# ==================== معلومات البوت ====================
اسم_الصانع = "معاذ أحمد أمين"

# ==================== الأسئلة ====================
أسئلة_البوت = []
سؤال_حالي = {}

# ==================== الكلمات المحظورة ====================
كلمات_محظورة = [
    "كس", "طيز", "زب", "شرموط", "عرص", "كلب", "حمار", "غبي", "أهبل", "تيس", "بهيم",
    "ابن متناكة", "ابن الوسخة", "ابن الكلب", "يلعن", "فشخ", "نيك", "متناك",
    "هقتلك", "هضربك", "هنعمل فيك",
    "عاهرة", "قحبة", "منيوك", "متناكة", "ابن الشرموطة", "يخرب بيتك",
    "يلعن دينك", "يلعن ابوك", "كسم", "كسمك", "طظ",
    "هبل", "احا", "اتنيل", "معرص", "خول", "خولة",
]

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
    {"الوقت": time(6, 0), "الرسالة": "🌅 *صباح الخير!*\n\nاللهم بارك لنا في يومنا ووفقنا للمذاكرة 📚\n\n💡 كل دقيقة تذاكر فيها هي خطوة نحو نجاحك ⭐"},
    {"الوقت": time(11, 0), "الرسالة": "☀️ *تذكير الظهر!*\n\nاللهم أعنّا على ذكرك وشكرك 🤲\n\n📚 وقت المذاكرة الذهبي! استغله 💡"},
    {"الوقت": time(18, 0), "الرسالة": "🌙 *مساء الخير!*\n\nاللهم اجعل ما تعلمناه نافعاً 🤲\n\n📖 راجع اللي ذاكرته النهارده قبل النوم 💪"},
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


def فيه_كلمة_محظورة(نص):
    نص_صغير = نص.lower()
    for كلمة in كلمات_محظورة:
        if كلمة in نص_صغير:
            return True
    return False


def فيه_رابط(نص):
    نمط = r'http[s]?://|www\.|t\.me/|bit\.ly/'
    return bool(re.search(نمط, نص, re.IGNORECASE))


def قراءة_أسئلة_من_ملف(file_bytes):
    global أسئلة_البوت
    أسئلة_البوت = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1] and row[2] and row[3] and row[4] and row[5]:
                أسئلة_البوت.append({
                    "سؤال": str(row[0]),
                    "إجابة": str(row[1]),
                    "أ": str(row[2]),
                    "ب": str(row[3]),
                    "ج": str(row[4]),
                    "د": str(row[5]),
                })
        return len(أسئلة_البوت)
    except Exception as خطأ:
        logging.error(f"خطأ في قراءة الملف: {خطأ}")
        return 0


async def إرسال_سؤال(context: ContextTypes.DEFAULT_TYPE):
    global سؤال_حالي
    if not أسئلة_البوت or CHAT_ID == 0:
        return

    سؤال_حالي = random.choice(أسئلة_البوت)
    نص = (
        f"🧠 *سؤال دراسي!*\n\n"
        f"❓ {سؤال_حالي['سؤال']}\n\n"
        f"أ) {سؤال_حالي['أ']}\n"
        f"ب) {سؤال_حالي['ب']}\n"
        f"ج) {سؤال_حالي['ج']}\n"
        f"د) {سؤال_حالي['د']}\n\n"
        f"⏱ عندك 60 ثانية للإجابة!"
    )
    أزرار = [[
        InlineKeyboardButton("أ", callback_data="إجابة_أ"),
        InlineKeyboardButton("ب", callback_data="إجابة_ب"),
        InlineKeyboardButton("ج", callback_data="إجابة_ج"),
        InlineKeyboardButton("د", callback_data="إجابة_د"),
    ]]
    await context.bot.send_message(CHAT_ID, نص, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(أزرار))
    context.job_queue.run_once(كشف_الإجابة, 60, data=سؤال_حالي)


async def كشف_الإجابة(context: ContextTypes.DEFAULT_TYPE):
    سؤال = context.job.data
    حرف = سؤال["إجابة"]
    نص_إجابة = سؤال[حرف]
    await context.bot.send_message(CHAT_ID, f"✅ *الإجابة الصحيحة:*\n\n{حرف}) {نص_إجابة}", parse_mode="Markdown")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user

    if OWNER_ID != 0 and مستخدم.id != OWNER_ID:
        يوزر = f"@{مستخدم.username}" if مستخدم.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"🆕 *مستخدم جديد!*\n\n👤 {مستخدم.first_name}\n🔗 {يوزر}\n🆔 `{مستخدم.id}`",
                parse_mode="Markdown"
            )
        except:
            pass

    رسالة = (
        "👋 *أهلاً! أنا بووووو — بوتك الإداري الذكي*\n\n"
        "أقدر أساعدك في:\n"
        "🔹 حظر وكتم الأعضاء المخالفين\n"
        "🔹 الترحيب بالأعضاء الجدد تلقائياً\n"
        "🔹 الرد على الأسئلة بالذكاء الاصطناعي\n"
        "🔹 فلترة الكلمات المسيئة والروابط\n"
        "🔹 إرسال أسئلة دراسية في الجروب\n\n"
        "⚡ *أوامر الإدارة — رد على رسالة العضو واكتب:*\n"
        "حظر | فك حظر | كتم | فك كتم | تحذير | مسح\n\n"
        "📚 *لرفع أسئلة:* ابعتلي ملف Excel في الخاص\n\n"
        "اختار من القائمة 👇"
    )
    await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    نتيجة = update.chat_member
    عضو_جديد = نتيجة.new_chat_member.user
    شات = update.effective_chat
    if نتيجة.new_chat_member.status == "member":
        await context.bot.send_message(
            شات.id,
            f"👋 *أهلاً وسهلاً {عضو_جديد.first_name}!*\n\nيسعدنا انضمامك لـ *{شات.title}* 🎉\n\n{قوانين_الجروب}",
            parse_mode="Markdown"
        )


async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    if بيانات.startswith("إجابة_"):
        حرف = بيانات.replace("إجابة_", "")
        if سؤال_حالي:
            if حرف == سؤال_حالي["إجابة"]:
                await query.answer("✅ إجابة صحيحة! 🎉", show_alert=True)
            else:
                await query.answer(f"❌ خاطئة! الصحيحة: {سؤال_حالي['إجابة']}", show_alert=True)
        return

    نصوص = {
        "مساعدة": (
            "📖 *دليل الاستخدام*\n\n"
            "رد على رسالة العضو واكتب:\n"
            "🔨 *حظر* | 🔓 *فك حظر*\n"
            "🔇 *كتم* | 🔊 *فك كتم*\n"
            "⚠️ *تحذير* | 🗑 *مسح*\n\n"
            "📚 *الأسئلة:* ابعت ملف Excel في الخاص\n"
            "🕐 *الجدولة:* قول 'ابعت كل X دقيقة' أو 'ابعت الساعة X'"
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


async def معالج_الملفات(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user
    if مستخدم.id != OWNER_ID:
        await update.message.reply_text("❌ هذه الميزة للأدمن فقط.")
        return

    document = update.message.document
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ ارفع ملف Excel بامتداد .xlsx فقط.")
        return

    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    عدد = قراءة_أسئلة_من_ملف(bytes(file_bytes))

    if عدد > 0:
        await update.message.reply_text(
            f"✅ تم رفع *{عدد}* سؤال بنجاح!\n\n"
            f"الآن قولي:\n"
            f"• *ابعت كل X دقيقة* — مثال: ابعت كل 30 دقيقة\n"
            f"• *ابعت الساعة X* — مثال: ابعت الساعة 3",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ مفيش أسئلة في الملف، تأكد من الشكل الصحيح.")


async def معالج_الرسائل(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    نص_الرسالة = update.message.text.strip()
    الرسالة_المردود_عليها = update.message.reply_to_message
    بوت_info = await context.bot.get_me()
    اسم_البوت = f"@{بوت_info.username}"
    في_الخاص = update.effective_chat.type == "private"
    مستخدم = update.effective_user

    # ==================== أوامر الأونر في الخاص ====================
    if في_الخاص and مستخدم.id == OWNER_ID:

        # جدولة كل X دقيقة
        match = re.match(r'ابعت كل (\d+) دقيقة', نص_الرسالة)
        if match:
            دقائق = int(match.group(1))
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            # إلغاء الجدول القديم
            jobs = context.job_queue.get_jobs_by_name("أسئلة")
            for job in jobs:
                job.schedule_removal()
            context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=10, name="أسئلة")
            await update.message.reply_text(f"✅ هيبعت سؤال كل *{دقائق}* دقيقة في الجروب 🎯", parse_mode="Markdown")
            return

        # جدولة في وقت معين
        match = re.match(r'ابعت الساعة (\d+)', نص_الرسالة)
        if match:
            ساعة = int(match.group(1))
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            jobs = context.job_queue.get_jobs_by_name("أسئلة_يومية")
            for job in jobs:
                job.schedule_removal()
            # تحويل للـ UTC
            ساعة_utc = (ساعة - 3) % 24
            context.job_queue.run_daily(إرسال_سؤال, time=time(ساعة_utc, 0), name="أسئلة_يومية")
            await update.message.reply_text(f"✅ هيبعت سؤال كل يوم الساعة *{ساعة}* 🎯", parse_mode="Markdown")
            return

        # وقف الأسئلة
        if نص_الرسالة in ["وقف الأسئلة", "وقف", "stop"]:
            jobs = context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("أسئلة_يومية")
            for job in jobs:
                job.schedule_removal()
            await update.message.reply_text("⏹ تم إيقاف إرسال الأسئلة.")
            return

        # سؤال الآن
        if نص_الرسالة in ["ابعت سؤال", "سؤال الآن"]:
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            await إرسال_سؤال(context)
            await update.message.reply_text("✅ تم إرسال سؤال في الجروب!")
            return

    # ==================== فلتر تلقائي ====================
    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص_الرسالة):
            try:
                await update.message.delete()
                if "تحذيرات" not in context.bot_data:
                    context.bot_data["تحذيرات"] = {}
                مفتاح = f"{update.effective_chat.id}_{مستخدم.id}"
                context.bot_data["تحذيرات"][مفتاح] = context.bot_data["تحذيرات"].get(مفتاح, 0) + 1
                عدد = context.bot_data["تحذيرات"][مفتاح]
                if عدد >= 3:
                    await context.bot.ban_chat_member(update.effective_chat.id, مستخدم.id)
                    context.bot_data["تحذيرات"][مفتاح] = 0
                    await context.bot.send_message(update.effective_chat.id, f"🚫 تم حظر {مستخدم.first_name} تلقائياً!")
                else:
                    await context.bot.send_message(update.effective_chat.id, f"⚠️ {مستخدم.first_name} تحذير {عدد}/3 بسبب كلمات مسيئة.")
            except Exception as خطأ:
                logging.error(f"فلتر: {خطأ}")
            return

        if فيه_رابط(نص_الرسالة):
            try:
                await update.message.delete()
                await context.bot.send_message(update.effective_chat.id, f"🔗 {مستخدم.first_name} ممنوع نشر الروابط!")
            except Exception as خطأ:
                logging.error(f"روابط: {خطأ}")
            return

    # ==================== أوامر الإدارة ====================
    if الرسالة_المردود_عليها and await هو_ادمن(update, context):
        عضو = الرسالة_المردود_عليها.from_user

        if نص_الرسالة == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔨 تم حظر {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص_الرسالة == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص_الرسالة == "كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, عضو.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص_الرسالة == "فك كتم":
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, عضو.id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False)
                )
                await update.message.reply_text(f"🔊 تم فك كتم {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص_الرسالة == "مسح":
            try:
                await الرسالة_المردود_عليها.delete()
                await update.message.delete()
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
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
                    await update.message.reply_text(f"🚫 تم حظر {عضو.first_name} بعد 3 تحذيرات!")
                except Exception as خطأ:
                    await update.message.reply_text(f"❌ {خطأ}")
            else:
                await update.message.reply_text(f"⚠️ تحذير {عدد}/3 لـ {عضو.first_name}")
            return

    if نص_الرسالة in ["القوانين", "قوانين", "rules"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return

    # ==================== الذكاء الاصطناعي ====================
    اتذكر = اسم_البوت.lower() in نص_الرسالة.lower()
    فيه_سؤال = "؟" in نص_الرسالة or "?" in نص_الرسالة

    if في_الخاص or اتذكر or فيه_سؤال:
        سؤال_نص = نص_الرسالة.replace(اسم_البوت, "").strip()
        if not سؤال_نص:
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
                            f"أنت مساعد ذكي اسمك بووووو، تم تطويرك وبرمجتك بواسطة {اسم_الصانع}. "
                            f"لو سألك أي شخص 'مين صنعك' أو 'مين برمجك' أو 'مين عملك'، قل إن الذي صنعك هو {اسم_الصانع}. "
                            "أنت مساعد في مجموعة تليجرام دراسية للصف الثاني الثانوي. "
                            "ردودك دائماً بالعربية، مختصرة ومفيدة."
                        )
                    },
                    {"role": "user", "content": سؤال_نص}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as خطأ:
            await update.message.reply_text(f"❌ حصل خطأ: {خطأ}")


async def إرسال_رسالة_مجدولة(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0:
        return
    await context.bot.send_message(CHAT_ID, context.job.data, parse_mode="Markdown")


def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.Document.ALL, معالج_الملفات))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))

    if CHAT_ID != 0:
        for رسالة in رسائل_مجدولة:
            تطبيق.job_queue.run_daily(إرسال_رسالة_مجدولة, time=رسالة["الوقت"], data=رسالة["الرسالة"])

    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
