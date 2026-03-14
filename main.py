"""
البوت الإداري الذكي - النسخة المتقدمة مع Supabase
=====================================================
متوافق مع python-telegram-bot==21.3 + Groq + Supabase
"""

import os
import re
import io
import logging
import random
from datetime import time
from groq import Groq
import openpyxl
from supabase import create_client
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
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

if not TOKEN:
    raise ValueError("❌ مفيش TOKEN")
if not GROQ_KEY:
    raise ValueError("❌ مفيش GROQ_KEY")

groq_client = Groq(api_key=GROQ_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

اسم_الصانع = "معاذ أحمد أمين"
أسئلة_البوت = []
سؤال_حالي = {}

كلمات_محظورة = [
    "كس", "طيز", "زب", "شرموط", "عرص", "كلب", "حمار", "غبي", "أهبل", "تيس", "بهيم",
    "ابن متناكة", "ابن الوسخة", "ابن الكلب", "يلعن", "فشخ", "نيك", "متناك",
    "هقتلك", "هضربك", "عاهرة", "قحبة", "منيوك", "متناكة", "ابن الشرموطة",
    "يلعن دينك", "يلعن ابوك", "كسم", "كسمك", "طظ", "احا", "اتنيل", "معرص", "خول",
]

قوانين_الجروب = """
📋 *قوانين الجروب*

1️⃣ الاحترام المتبادل بين الأعضاء
2️⃣ ممنوع السب والشتيمة
3️⃣ ممنوع الإعلانات والسبام
4️⃣ ممنوع نشر روابط بدون إذن
5️⃣ الالتزام بموضوع الجروب

⚠️ مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي.
"""

رسائل_مجدولة = [
    {"الوقت": time(6, 0), "الرسالة": "🌅 *صباح الخير!*\n\nاللهم بارك لنا في يومنا ووفقنا للمذاكرة 📚\n\n💡 كل دقيقة تذاكر فيها هي خطوة نحو نجاحك ⭐"},
    {"الوقت": time(11, 0), "الرسالة": "☀️ *تذكير الظهر!*\n\nاللهم أعنّا على ذكرك وشكرك 🤲\n\n📚 وقت المذاكرة الذهبي! استغله 💡"},
    {"الوقت": time(18, 0), "الرسالة": "🌙 *مساء الخير!*\n\nاللهم اجعل ما تعلمناه نافعاً 🤲\n\n📖 راجع اللي ذاكرته النهارده قبل النوم 💪"},
]


# ==================== Supabase Functions ====================
def جيب_تحذيرات(chat_id, user_id):
    if not supabase:
        return 0
    try:
        res = supabase.table("تحذيرات").select("عدد").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]["عدد"]
        return 0
    except:
        return 0


def حدث_تحذيرات(chat_id, user_id, عدد):
    if not supabase:
        return
    try:
        res = supabase.table("تحذيرات").select("id").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        if res.data:
            supabase.table("تحذيرات").update({"عدد": عدد}).eq("chat_id", chat_id).eq("user_id", user_id).execute()
        else:
            supabase.table("تحذيرات").insert({"chat_id": chat_id, "user_id": user_id, "عدد": عدد}).execute()
    except Exception as خطأ:
        logging.error(f"Supabase تحذيرات: {خطأ}")


def سجل_مستخدم(user_id, الاسم, يوزرنيم):
    if not supabase:
        return
    try:
        res = supabase.table("مستخدمين").select("id").eq("user_id", user_id).execute()
        if not res.data:
            supabase.table("مستخدمين").insert({
                "user_id": user_id,
                "الاسم": الاسم,
                "يوزرنيم": يوزرنيم
            }).execute()
    except Exception as خطأ:
        logging.error(f"Supabase مستخدمين: {خطأ}")


def جيب_إحصائيات():
    if not supabase:
        return None
    try:
        مستخدمين = supabase.table("مستخدمين").select("*", count="exact").execute()
        محذرين = supabase.table("تحذيرات").select("*").gt("عدد", 0).execute()
        return {
            "مستخدمين": مستخدمين.count or 0,
            "محذرين": len(محذرين.data) if محذرين.data else 0,
        }
    except:
        return None


# ==================== Helper Functions ====================
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
            InlineKeyboardButton("📊 إحصائيات", callback_data="إحصائيات"),
        ],
        [
            InlineKeyboardButton("❓ المساعدة", callback_data="مساعدة"),
        ],
    ]
    return InlineKeyboardMarkup(أزرار)


async def هو_ادمن(update, context):
    مستخدم = update.effective_user
    شات = update.effective_chat
    if شات.type == "private":
        return True
    عضو = await context.bot.get_chat_member(شات.id, مستخدم.id)
    return عضو.status in ["administrator", "creator"]


def فيه_كلمة_محظورة(نص):
    نص_صغير = نص.lower()
    for كلمة in كلمات_محظورة:
        if كلمة in نص_صغير:
            return True
    return False


def فيه_رابط(نص):
    return bool(re.search(r'http[s]?://|www\.|t\.me/|bit\.ly/', نص, re.IGNORECASE))


def قراءة_أسئلة(file_bytes):
    global أسئلة_البوت
    أسئلة_البوت = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if all(row[:6]):
                أسئلة_البوت.append({
                    "سؤال": str(row[0]), "إجابة": str(row[1]),
                    "أ": str(row[2]), "ب": str(row[3]),
                    "ج": str(row[4]), "د": str(row[5]),
                })
        return len(أسئلة_البوت)
    except Exception as خطأ:
        logging.error(f"قراءة ملف: {خطأ}")
        return 0


async def إرسال_سؤال(context: ContextTypes.DEFAULT_TYPE):
    global سؤال_حالي
    if not أسئلة_البوت or CHAT_ID == 0:
        return
    سؤال_حالي = random.choice(أسئلة_البوت)
    نص = (
        f"🧠 *سؤال دراسي!*\n\n❓ {سؤال_حالي['سؤال']}\n\n"
        f"أ) {سؤال_حالي['أ']}\nب) {سؤال_حالي['ب']}\n"
        f"ج) {سؤال_حالي['ج']}\nد) {سؤال_حالي['د']}\n\n⏱ عندك 60 ثانية!"
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
    await context.bot.send_message(CHAT_ID, f"✅ *الإجابة:* {حرف}) {سؤال[حرف]}", parse_mode="Markdown")


# ==================== Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user
    سجل_مستخدم(مستخدم.id, مستخدم.first_name, مستخدم.username or "")

    if OWNER_ID != 0 and مستخدم.id != OWNER_ID:
        يوزر = f"@{مستخدم.username}" if مستخدم.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n\n👤 {مستخدم.first_name}\n🔗 {يوزر}\n🆔 `{مستخدم.id}`", parse_mode="Markdown")
        except:
            pass

    await update.message.reply_text(
        "👋 *أهلاً! أنا بووووو — بوتك الإداري الذكي*\n\n"
        "🔹 حظر وكتم الأعضاء المخالفين\n"
        "🔹 الترحيب بالأعضاء الجدد تلقائياً\n"
        "🔹 الرد على الأسئلة بالذكاء الاصطناعي\n"
        "🔹 فلترة الكلمات المسيئة والروابط\n"
        "🔹 أسئلة دراسية في الجروب\n\n"
        "📚 *لرفع أسئلة:* ابعتلي ملف Excel في الخاص\n\n"
        "اختار من القائمة 👇",
        parse_mode="Markdown",
        reply_markup=القائمة_الرئيسية()
    )


async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    نتيجة = update.chat_member
    عضو_جديد = نتيجة.new_chat_member.user
    شات = update.effective_chat
    if نتيجة.new_chat_member.status == "member":
        سجل_مستخدم(عضو_جديد.id, عضو_جديد.first_name, عضو_جديد.username or "")
        await context.bot.send_message(
            شات.id,
            f"👋 *أهلاً {عضو_جديد.first_name}!*\n\nيسعدنا انضمامك لـ *{شات.title}* 🎉\n\n{قوانين_الجروب}",
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

    if بيانات == "إحصائيات":
        إحصاء = جيب_إحصائيات()
        if إحصاء:
            نص = (
                f"📊 *إحصائيات البوت*\n\n"
                f"👥 المستخدمين: *{إحصاء['مستخدمين']}*\n"
                f"⚠️ الأعضاء المحذرين: *{إحصاء['محذرين']}*\n"
                f"📚 الأسئلة المحملة: *{len(أسئلة_البوت)}*"
            )
        else:
            نص = "📊 *إحصائيات البوت*\n\n🚧 جاري تحميل البيانات..."
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())
        return

    نصوص = {
        "مساعدة": (
            "📖 *دليل الاستخدام*\n\n"
            "رد على رسالة العضو واكتب:\n"
            "🔨 *حظر* | 🔓 *فك حظر*\n"
            "🔇 *كتم* | 🔊 *فك كتم*\n"
            "⚠️ *تحذير* | 🗑 *مسح*\n\n"
            "📚 *الأسئلة من الخاص:*\n"
            "• ابعت كل X دقيقة\n"
            "• ابعت الساعة X\n"
            "• ابعت سؤال\n"
            "• وقف الأسئلة"
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
        await update.message.reply_text("❌ ارفع ملف Excel .xlsx فقط.")
        return
    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    عدد = قراءة_أسئلة(bytes(file_bytes))
    if عدد > 0:
        await update.message.reply_text(
            f"✅ تم رفع *{عدد}* سؤال!\n\n"
            "قولي:\n• *ابعت كل X دقيقة*\n• *ابعت الساعة X*\n• *ابعت سؤال*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ مفيش أسئلة في الملف.")


async def معالج_الرسائل(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    نص = update.message.text.strip()
    مردود_عليه = update.message.reply_to_message
    بوت_info = await context.bot.get_me()
    اسم_البوت = f"@{بوت_info.username}"
    في_الخاص = update.effective_chat.type == "private"
    مستخدم = update.effective_user

    # أوامر الأونر
    if في_الخاص and مستخدم.id == OWNER_ID:
        match = re.match(r'ابعت كل (\d+) دقيقة', نص)
        if match:
            دقائق = int(match.group(1))
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            for job in context.job_queue.get_jobs_by_name("أسئلة"):
                job.schedule_removal()
            context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=10, name="أسئلة")
            await update.message.reply_text(f"✅ هيبعت سؤال كل *{دقائق}* دقيقة 🎯", parse_mode="Markdown")
            return

        match = re.match(r'ابعت الساعة (\d+)', نص)
        if match:
            ساعة = int(match.group(1))
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            for job in context.job_queue.get_jobs_by_name("أسئلة_يومية"):
                job.schedule_removal()
            ساعة_utc = (ساعة - 3) % 24
            context.job_queue.run_daily(إرسال_سؤال, time=time(ساعة_utc, 0), name="أسئلة_يومية")
            await update.message.reply_text(f"✅ هيبعت سؤال كل يوم الساعة *{ساعة}* 🎯", parse_mode="Markdown")
            return

        if نص in ["وقف الأسئلة", "وقف", "stop"]:
            for job in context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("أسئلة_يومية"):
                job.schedule_removal()
            await update.message.reply_text("⏹ تم إيقاف الأسئلة.")
            return

        if نص in ["ابعت سؤال", "سؤال الآن"]:
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            await إرسال_سؤال(context)
            await update.message.reply_text("✅ تم إرسال سؤال!")
            return

    # فلتر تلقائي
    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص):
            try:
                await update.message.delete()
                عدد_ح = جيب_تحذيرات(update.effective_chat.id, مستخدم.id) + 1
                حدث_تحذيرات(update.effective_chat.id, مستخدم.id, عدد_ح)
                if عدد_ح >= 3:
                    await context.bot.ban_chat_member(update.effective_chat.id, مستخدم.id)
                    حدث_تحذيرات(update.effective_chat.id, مستخدم.id, 0)
                    await context.bot.send_message(update.effective_chat.id, f"🚫 تم حظر {مستخدم.first_name} تلقائياً!")
                else:
                    await context.bot.send_message(update.effective_chat.id, f"⚠️ {مستخدم.first_name} تحذير {عدد_ح}/3")
            except Exception as خطأ:
                logging.error(f"فلتر: {خطأ}")
            return

        if فيه_رابط(نص):
            try:
                await update.message.delete()
                await context.bot.send_message(update.effective_chat.id, f"🔗 {مستخدم.first_name} ممنوع الروابط!")
            except Exception as خطأ:
                logging.error(f"روابط: {خطأ}")
            return

    # أوامر الإدارة
    if مردود_عليه and await هو_ادمن(update, context):
        عضو = مردود_عليه.from_user

        if نص == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔨 تم حظر {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص == "كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, عضو.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص == "فك كتم":
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, عضو.id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False)
                )
                await update.message.reply_text(f"🔊 تم فك كتم {عضو.first_name}.")
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص == "مسح":
            try:
                await مردود_عليه.delete()
                await update.message.delete()
            except Exception as خطأ:
                await update.message.reply_text(f"❌ {خطأ}")
            return

        elif نص == "تحذير":
            عدد_ح = جيب_تحذيرات(update.effective_chat.id, عضو.id) + 1
            حدث_تحذيرات(update.effective_chat.id, عضو.id, عدد_ح)
            if عدد_ح >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                    حدث_تحذيرات(update.effective_chat.id, عضو.id, 0)
                    await update.message.reply_text(f"🚫 تم حظر {عضو.first_name} بعد 3 تحذيرات!")
                except Exception as خطأ:
                    await update.message.reply_text(f"❌ {خطأ}")
            else:
                await update.message.reply_text(f"⚠️ تحذير {عدد_ح}/3 لـ {عضو.first_name}")
            return

    if نص in ["القوانين", "قوانين", "rules"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return

    # الذكاء الاصطناعي
    اتذكر = اسم_البوت.lower() in نص.lower()
    فيه_سؤال = "؟" in نص or "?" in نص

    if في_الخاص or اتذكر or فيه_سؤال:
        سؤال_نص = نص.replace(اسم_البوت, "").strip()
        if not سؤال_نص:
            return
        try:
            await context.bot.send_chat_action(update.effective_chat.id, "typing")
            رد = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": f"أنت مساعد ذكي اسمك بووووو، صنعك {اسم_الصانع}. لو سألك أي شخص مين صنعك قل {اسم_الصانع}. أنت في جروب دراسي للصف الثاني الثانوي. ردودك بالعربية ومختصرة."},
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
