"""
البوت الإداري الذكي - النسخة النهائية
========================================
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
    raise ValueError("مفيش TOKEN")
if not GROQ_KEY:
    raise ValueError("مفيش GROQ_KEY")

groq_client = Groq(api_key=GROQ_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

اسم_الصانع = "Moaz"
أسئلة_البوت = []
سؤال_حالي = {}

كلمات_محظورة = [
    "كس", "طيز", "زب", "شرموط", "عرص", "كلب", "حمار", "غبي", "أهبل", "تيس", "بهيم",
    "ابن متناكة", "ابن الوسخة", "ابن الكلب", "يلعن", "فشخ", "نيك", "متناك",
    "هقتلك", "هضربك", "عاهرة", "قحبة", "منيوك", "متناكة", "ابن الشرموطة",
    "يلعن دينك", "يلعن ابوك", "كسم", "كسمك", "طظ", "احا", "اتنيل", "معرص", "خول", "خولة",
]

قوانين_الجروب = (
    "📋 *قوانين الجروب*\n\n"
    "1️⃣ الاحترام المتبادل بين الأعضاء\n"
    "2️⃣ ممنوع السب والشتيمة\n"
    "3️⃣ ممنوع الإعلانات والسبام\n"
    "4️⃣ ممنوع نشر روابط بدون إذن\n"
    "5️⃣ الالتزام بموضوع الجروب\n\n"
    "⚠️ مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي."
)

رسائل_مجدولة = [
    {"الوقت": time(6, 0), "الرسالة": "🌅 *صباح الخير!*\n\nاللهم بارك لنا في يومنا ووفقنا للمذاكرة 📚\n\n💡 كل دقيقة تذاكر فيها هي خطوة نحو نجاحك ⭐"},
    {"الوقت": time(11, 0), "الرسالة": "☀️ *تذكير الظهر!*\n\nاللهم أعنّا على ذكرك وشكرك 🤲\n\n📚 وقت المذاكرة الذهبي! استغله 💡"},
    {"الوقت": time(18, 0), "الرسالة": "🌙 *مساء الخير!*\n\nاللهم اجعل ما تعلمناه نافعاً 🤲\n\n📖 راجع اللي ذاكرته النهارده قبل النوم 💪"},
]


# ==================== Supabase ====================

async def جيب_تحذيرات(chat_id, user_id):
    if not supabase:
        return 0
    try:
        result = supabase.table("تحذيرات").select("عدد").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]["عدد"]
        return 0
    except Exception as e:
        logging.error(f"جيب_تحذيرات: {e}")
        return 0


async def حدث_تحذيرات(chat_id, user_id, عدد):
    if not supabase:
        return
    try:
        existing = supabase.table("تحذيرات").select("id").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        if existing.data:
            supabase.table("تحذيرات").update({"عدد": عدد}).eq("chat_id", chat_id).eq("user_id", user_id).execute()
        else:
            supabase.table("تحذيرات").insert({"chat_id": chat_id, "user_id": user_id, "عدد": عدد}).execute()
    except Exception as e:
        logging.error(f"حدث_تحذيرات: {e}")


async def سجل_مستخدم(user_id, الاسم, يوزرنيم):
    if not supabase:
        return
    try:
        existing = supabase.table("مستخدمين").select("id").eq("user_id", user_id).execute()
        if not existing.data:
            supabase.table("مستخدمين").insert({"user_id": user_id, "الاسم": الاسم, "يوزرنيم": يوزرنيم or ""}).execute()
    except Exception as e:
        logging.error(f"سجل_مستخدم: {e}")


async def جيب_إحصائيات():
    if not supabase:
        return None
    try:
        مستخدمين = supabase.table("مستخدمين").select("*", count="exact").execute()
        محذورين = supabase.table("تحذيرات").select("*").gte("عدد", 1).execute()
        return {
            "مستخدمين": مستخدمين.count or 0,
            "محذورين": len(محذورين.data) if محذورين.data else 0,
        }
    except Exception as e:
        logging.error(f"جيب_إحصائيات: {e}")
        return None


# ==================== قوائم ====================

def القائمة_الرئيسية():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔨 حظر عضو", callback_data="حظر"), InlineKeyboardButton("🔓 فك الحظر", callback_data="فك_حظر")],
        [InlineKeyboardButton("🔇 كتم عضو", callback_data="كتم"), InlineKeyboardButton("🔊 فك الكتم", callback_data="فك_كتم")],
        [InlineKeyboardButton("⚠️ تحذير", callback_data="تحذير"), InlineKeyboardButton("🗑 مسح رسالة", callback_data="مسح")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="إحصائيات"), InlineKeyboardButton("📋 القوانين", callback_data="قوانين")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="مساعدة")],
    ])


def قائمة_التحكم():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات", callback_data="ctrl_إحصائيات"), InlineKeyboardButton("❓ سؤال الآن", callback_data="ctrl_سؤال")],
        [InlineKeyboardButton("⏹ وقف الأسئلة", callback_data="ctrl_وقف"), InlineKeyboardButton("📋 القوانين", callback_data="ctrl_قوانين")],
        [InlineKeyboardButton("🔒 قفل الجروب", callback_data="ctrl_قفل"), InlineKeyboardButton("🔓 فتح الجروب", callback_data="ctrl_فتح")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="ctrl_رئيسية")],
    ])


# ==================== دوال مساعدة ====================

async def هو_ادمن(update, context):
    مستخدم = update.effective_user
    شات = update.effective_chat
    if شات.type == "private":
        return True
    عضو = await context.bot.get_chat_member(شات.id, مستخدم.id)
    return عضو.status in ["administrator", "creator"]


def فيه_كلمة_محظورة(نص):
    نص_صغير = نص.lower()
    return any(كلمة in نص_صغير for كلمة in كلمات_محظورة)


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
                    "أ": str(row[2]), "ب": str(row[3]), "ج": str(row[4]), "د": str(row[5]),
                })
        return len(أسئلة_البوت)
    except Exception as e:
        logging.error(f"قراءة_أسئلة: {e}")
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
        f"⏱ عندك 60 ثانية!"
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
    await context.bot.send_message(CHAT_ID, f"✅ *الإجابة الصحيحة:*\n\n{حرف}) {سؤال[حرف]}", parse_mode="Markdown")


# ==================== Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user
    await سجل_مستخدم(مستخدم.id, مستخدم.first_name, مستخدم.username)

    if OWNER_ID != 0 and مستخدم.id != OWNER_ID:
        يوزر = f"@{مستخدم.username}" if مستخدم.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n\n👤 {مستخدم.first_name}\n🔗 {يوزر}\n🆔 `{مستخدم.id}`", parse_mode="Markdown")
        except:
            pass

    رسالة = (
        "👋 *أهلاً! أنا بووووو — بوتك الإداري الذكي*\n\n"
        "🔹 حظر وكتم الأعضاء\n"
        "🔹 ترحيب بالأعضاء الجدد\n"
        "🔹 ذكاء اصطناعي يرد على الأسئلة\n"
        "🔹 فلتر الكلمات والروابط\n"
        "🔹 أسئلة دراسية في الجروب\n\n"
        "اختار من القائمة 👇"
    )
    await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def لوحة_التحكم(update: Update, context: ContextTypes.DEFAULT_TYPE):
    مستخدم = update.effective_user
    if مستخدم.id != OWNER_ID:
        await update.message.reply_text("❌ هذه الميزة للأدمن فقط.")
        return

    إحصاء = await جيب_إحصائيات()
    نص = (
        "🎛 *لوحة التحكم*\n\n"
        f"👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n"
        f"⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n"
        f"📚 الأسئلة: {len(أسئلة_البوت)}\n\n"
        "اختار من الأزرار 👇"
    )
    await update.message.reply_text(نص, parse_mode="Markdown", reply_markup=قائمة_التحكم())


async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    نتيجة = update.chat_member
    عضو_جديد = نتيجة.new_chat_member.user
    شات = update.effective_chat
    if نتيجة.new_chat_member.status == "member":
        await سجل_مستخدم(عضو_جديد.id, عضو_جديد.first_name, عضو_جديد.username)
        await context.bot.send_message(شات.id, f"👋 *أهلاً {عضو_جديد.first_name}!*\n\nيسعدنا انضمامك لـ *{شات.title}* 🎉\n\n{قوانين_الجروب}", parse_mode="Markdown")


async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    # إجابة سؤال
    if بيانات.startswith("إجابة_"):
        حرف = بيانات.replace("إجابة_", "")
        if سؤال_حالي:
            if حرف == سؤال_حالي["إجابة"]:
                await query.answer("✅ إجابة صحيحة! 🎉", show_alert=True)
            else:
                await query.answer(f"❌ خاطئة! الصحيحة: {سؤال_حالي['إجابة']}", show_alert=True)
        return

    # أزرار لوحة التحكم
    if بيانات.startswith("ctrl_"):
        أمر = بيانات.replace("ctrl_", "")

        if أمر == "إحصائيات":
            إحصاء = await جيب_إحصائيات()
            نص = (
                f"📊 *الإحصائيات*\n\n"
                f"👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n"
                f"⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n"
                f"📚 الأسئلة: {len(أسئلة_البوت)}"
            )
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=قائمة_التحكم())

        elif أمر == "سؤال":
            if not أسئلة_البوت:
                await query.answer("❌ ارفع ملف الأسئلة الأول!", show_alert=True)
            else:
                await إرسال_سؤال(context)
                await query.answer("✅ تم إرسال سؤال في الجروب!", show_alert=True)

        elif أمر == "وقف":
            for job in context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("أسئلة_يومية"):
                job.schedule_removal()
            await query.answer("⏹ تم وقف الأسئلة.", show_alert=True)

        elif أمر == "قوانين":
            await query.edit_message_text(قوانين_الجروب, parse_mode="Markdown", reply_markup=قائمة_التحكم())

        elif أمر == "قفل":
            if CHAT_ID == 0:
                await query.answer("❌ ضيف CHAT_ID في Railway!", show_alert=True)
            else:
                try:
                    await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=False, can_send_polls=False, can_send_other_messages=False, can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                    await context.bot.send_message(CHAT_ID, "🔒 *تم قفل الجروب مؤقتاً*", parse_mode="Markdown")
                    await query.answer("✅ تم قفل الجروب.", show_alert=True)
                except Exception as e:
                    await query.answer(f"❌ فشل: {e}", show_alert=True)

        elif أمر == "فتح":
            if CHAT_ID == 0:
                await query.answer("❌ ضيف CHAT_ID في Railway!", show_alert=True)
            else:
                try:
                    await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False))
                    await context.bot.send_message(CHAT_ID, "🔓 *تم فتح الجروب*", parse_mode="Markdown")
                    await query.answer("✅ تم فتح الجروب.", show_alert=True)
                except Exception as e:
                    await query.answer(f"❌ فشل: {e}", show_alert=True)

        elif أمر == "رئيسية":
            await query.edit_message_text("اختار من القائمة 👇", reply_markup=القائمة_الرئيسية())
        return

    # أزرار القائمة الرئيسية
    if بيانات == "إحصائيات":
        إحصاء = await جيب_إحصائيات()
        نص = (
            f"📊 *إحصائيات البوت*\n\n"
            f"👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n"
            f"⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n"
            f"📚 الأسئلة: {len(أسئلة_البوت)}"
        )
        await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=القائمة_الرئيسية())
        return

    نصوص = {
        "مساعدة": (
            "📖 *دليل الاستخدام*\n\n"
            "رد على رسالة العضو واكتب:\n"
            "🔨 *حظر* | 🔓 *فك حظر*\n"
            "🔇 *كتم* | 🔊 *فك كتم*\n"
            "⚠️ *تحذير* | 🗑 *مسح*\n\n"
            "📚 ابعت ملف Excel في الخاص للأسئلة\n"
            "🎛 اكتب /ctrl للوحة التحكم"
        ),
        "قوانين": قوانين_الجروب,
        "حظر": "🔨 *حظر عضو*\n\nرد على رسالة العضو واكتب:\n*حظر*",
        "فك_حظر": "🔓 *فك الحظر*\n\nرد على رسالة العضو واكتب:\n*فك حظر*",
        "كتم": "🔇 *كتم عضو*\n\nرد على رسالة العضو واكتب:\n*كتم*",
        "فك_كتم": "🔊 *فك الكتم*\n\nرد على رسالة العضو واكتب:\n*فك كتم*",
        "تحذير": "⚠️ *التحذيرات*\n\nرد على رسالة العضو واكتب:\n*تحذير*\n\n📌 بعد 3 تحذيرات = حظر تلقائي",
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
    عدد = قراءة_أسئلة(bytes(file_bytes))

    if عدد > 0:
        await update.message.reply_text(
            f"✅ تم رفع *{عدد}* سؤال!\n\n"
            f"• *ابعت كل X دقيقة*\n"
            f"• *ابعت الساعة X*\n"
            f"• *ابعت سؤال* — فوراً",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ مفيش أسئلة في الملف.")


async def معالج_الرسائل(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    نص = update.message.text.strip()
    رد_على = update.message.reply_to_message
    بوت_info = await context.bot.get_me()
    اسم_البوت = f"@{بوت_info.username}"
    في_الخاص = update.effective_chat.type == "private"
    مستخدم = update.effective_user

    # أوامر الأونر في الخاص
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
            await update.message.reply_text("✅ تم إرسال سؤال في الجروب!")
            return

        if نص in ["اقفل الجروب", "قفل الجروب"]:
            if CHAT_ID == 0:
                await update.message.reply_text("❌ ضيف CHAT_ID في Railway الأول!")
                return
            try:
                await context.bot.set_chat_permissions(
                    CHAT_ID,
                    ChatPermissions(
                        can_send_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                    )
                )
                await context.bot.send_message(CHAT_ID, "🔒 *تم قفل الجروب مؤقتاً*\nلا يمكن لأي عضو إرسال رسائل الآن.", parse_mode="Markdown")
                await update.message.reply_text("✅ تم قفل الجروب.")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل القفل: {e}")
            return

        if نص in ["افتح الجروب", "فتح الجروب"]:
            if CHAT_ID == 0:
                await update.message.reply_text("❌ ضيف CHAT_ID في Railway الأول!")
                return
            try:
                await context.bot.set_chat_permissions(
                    CHAT_ID,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=False,
                    )
                )
                await context.bot.send_message(CHAT_ID, "🔓 *تم فتح الجروب*\nيمكن للأعضاء الكلام الآن.", parse_mode="Markdown")
                await update.message.reply_text("✅ تم فتح الجروب.")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل الفتح: {e}")
            return

    # فلتر تلقائي
    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص):
            try:
                await update.message.delete()
                عدد_حالي = await جيب_تحذيرات(update.effective_chat.id, مستخدم.id)
                عدد_جديد = عدد_حالي + 1
                await حدث_تحذيرات(update.effective_chat.id, مستخدم.id, عدد_جديد)
                if عدد_جديد >= 3:
                    await context.bot.ban_chat_member(update.effective_chat.id, مستخدم.id)
                    await حدث_تحذيرات(update.effective_chat.id, مستخدم.id, 0)
                    await context.bot.send_message(update.effective_chat.id, f"🚫 تم حظر {مستخدم.first_name} تلقائياً!")
                else:
                    await context.bot.send_message(update.effective_chat.id, f"⚠️ {مستخدم.first_name} تحذير {عدد_جديد}/3")
            except Exception as e:
                logging.error(f"فلتر: {e}")
            return

        if فيه_رابط(نص):
            try:
                await update.message.delete()
                await context.bot.send_message(update.effective_chat.id, f"🔗 {مستخدم.first_name} ممنوع نشر الروابط!")
            except Exception as e:
                logging.error(f"روابط: {e}")
            return

    # أوامر الإدارة
    if رد_على and await هو_ادمن(update, context):
        عضو = رد_على.from_user

        if نص == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔨 تم حظر {عضو.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        elif نص == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, عضو.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {عضو.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        elif نص == "كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, عضو.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {عضو.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        elif نص == "فك كتم":
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, عضو.id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False)
                )
                await update.message.reply_text(f"🔊 تم فك كتم {عضو.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        elif نص == "مسح":
            try:
                await رد_على.delete()
                await update.message.delete()
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        elif نص == "تحذير":
            عدد_حالي = await جيب_تحذيرات(update.effective_chat.id, عضو.id)
            عدد_جديد = عدد_حالي + 1
            await حدث_تحذيرات(update.effective_chat.id, عضو.id, عدد_جديد)
            if عدد_جديد >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, عضو.id)
                    await حدث_تحذيرات(update.effective_chat.id, عضو.id, 0)
                    await update.message.reply_text(f"🚫 تم حظر {عضو.first_name} بعد 3 تحذيرات!")
                except Exception as e:
                    await update.message.reply_text(f"❌ {e}")
            else:
                await update.message.reply_text(f"⚠️ تحذير {عدد_جديد}/3 لـ {عضو.first_name}")
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
                    {
                        "role": "system",
                        "content": (
                            f"أنت مساعد ذكي اسمك بووووو، صنعك {اسم_الصانع}. "
                            f"لو سألك أي شخص مين صنعك، قول إن اللي صنعك هو {اسم_الصانع}. "
                            "أنت في جروب دراسي للصف الثاني الثانوي. ردودك بالعربية، مختصرة ومفيدة."
                        )
                    },
                    {"role": "user", "content": سؤال_نص}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"❌ حصل خطأ: {e}")


async def إرسال_رسالة_مجدولة(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0:
        return
    await context.bot.send_message(CHAT_ID, context.job.data, parse_mode="Markdown")


def main():
    تطبيق = ApplicationBuilder().token(TOKEN).build()

    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("ctrl", لوحة_التحكم))
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
