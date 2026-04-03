import os, re, io, logging, random
from datetime import time
from groq import Groq
import openpyxl
from supabase import create_client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, ContextTypes, filters,
)

TOKEN = os.environ.get("TOKEN")
GROQ_KEY = os.environ.get("GROQ_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

if not TOKEN: raise ValueError("مفيش TOKEN")
if not GROQ_KEY: raise ValueError("مفيش GROQ_KEY")

groq_client = Groq(api_key=GROQ_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

اسم_الصانع = "Moaz"
أسئلة_البوت = []
سؤال_حالي = {}
معسكر_info = {"اسم_المادة": "", "كل_دقايق": 1}
إحصائيات_معسكر = {"أسئلة_بُعتت": 0}
index_سؤال = 0
أسئلة_مخلوطة = []

رسائل_تحفيزية = [
    "💪 *استمر! كل سؤال بتجاوبه هو خطوة نحو النجاح!*\n✨ العلم نور والجهل ظلام",
    "🔥 *أنت أقوى مما تتخيل!*\n📚 المذاكرة اليوم = نجاح الغد",
    "⭐ *لا تستسلم! المثابرة هي مفتاح التفوق!*\n🎯 ركز وانت هتوصل",
    "🌟 *كل لحظة مذاكرة هي استثمار في مستقبلك!*\n💡 الذكاء يصنع بالمجهود",
    "🚀 *أنت في الطريق الصح!*\n📖 اللي بيذاكر دلوقتي بيحصد غداً",
    "💎 *العلم كنز لا يسرق!*\n🎓 اجتهد وتوكل على الله",
    "🌈 *النجاح حلم + عمل + إيمان!*\n⚡ انت قادر تحقق كل حاجة",
    "🏆 *المتفوقون اجتهدوا!*\n💫 إجتهادك هيفرق",
]

أذكار = [
    "🤲 *اللهم صل وسلم على سيدنا محمد*\n💝 اللهم صل على النبي عدد ما خلقت",
    "🌸 *سبحان الله وبحمده*\n✨ سبحان الله العظيم",
    "💚 *استغفر الله العظيم وأتوب إليه*\n🌿 اللهم اغفر لي وتب علي",
    "⭐ *الحمد لله على كل حال*\n🌟 الحمد لله الذي بنعمته تتم الصالحات",
    "🤍 *لا إله إلا الله محمد رسول الله*\n💫 لا إله إلا أنت سبحانك",
    "🌙 *اللهم اجعل علمنا نافعاً*\n📚 اللهم علمنا ما ينفعنا",
    "💛 *اللهم أعنا على ذكرك وشكرك*\n🌺 ربنا آتنا في الدنيا حسنة",
    "🌹 *اللهم بارك لنا في أوقاتنا*\n✨ اللهم وفقنا لما تحب وترضى",
]

كلمات_محظورة = [
    "كس", "طيز", "زب", "شرموط", "عرص", "كلب", "حمار", "غبي", "أهبل", "تيس", "بهيم",
    "ابن متناكة", "ابن الوسخة", "ابن الكلب", "يلعن", "فشخ", "نيك", "متناك",
    "هقتلك", "هضربك", "عاهرة", "قحبة", "منيوك", "متناكة", "ابن الشرموطة",
    "يلعن دينك", "يلعن ابوك", "كسم", "كسمك", "طظ", "احا", "اتنيل", "معرص", "خول", "خولة",
]

قوانين_الجروب = (
    "📋 *قوانين الجروب*\n\n"
    "1 الاحترام المتبادل\n"
    "2 ممنوع السب والشتيمة\n"
    "3 ممنوع الاعلانات والسبام\n"
    "4 ممنوع نشر روابط بدون اذن\n"
    "5 الالتزام بموضوع الجروب\n\n"
    "مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي."
)

رسائل_مجدولة = [
    {"الوقت": time(6, 0), "الرسالة": "🌅 *صباح الخير!*\n\nاللهم بارك لنا في يومنا 📚"},
    {"الوقت": time(11, 0), "الرسالة": "☀️ *تذكير الظهر!*\n\nوقت المذاكرة الذهبي 💡"},
    {"الوقت": time(18, 0), "الرسالة": "🌙 *مساء الخير!*\n\nراجع اللي ذاكرته قبل النوم 💪"},
]


# ==================== Supabase ====================
async def جيب_تحذيرات(chat_id, user_id):
    if not supabase: return 0
    try:
        r = supabase.table("تحذيرات").select("عدد").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        return r.data[0]["عدد"] if r.data else 0
    except: return 0

async def حدث_تحذيرات(chat_id, user_id, عدد):
    if not supabase: return
    try:
        e = supabase.table("تحذيرات").select("id").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        if e.data:
            supabase.table("تحذيرات").update({"عدد": عدد}).eq("chat_id", chat_id).eq("user_id", user_id).execute()
        else:
            supabase.table("تحذيرات").insert({"chat_id": chat_id, "user_id": user_id, "عدد": عدد}).execute()
    except: pass

async def سجل_مستخدم(user_id, الاسم, يوزرنيم):
    if not supabase: return
    try:
        e = supabase.table("مستخدمين").select("id").eq("user_id", user_id).execute()
        if not e.data:
            supabase.table("مستخدمين").insert({"user_id": user_id, "الاسم": الاسم, "يوزرنيم": يوزرنيم or ""}).execute()
    except: pass

async def سجل_جروب(chat_id, اسم):
    if not supabase: return
    try:
        e = supabase.table("جروبات").select("id").eq("chat_id", chat_id).execute()
        if not e.data:
            supabase.table("جروبات").insert({"chat_id": chat_id, "اسم": اسم}).execute()
        else:
            supabase.table("جروبات").update({"اسم": اسم}).eq("chat_id", chat_id).execute()
    except Exception as ex:
        logging.error(f"سجل_جروب: {ex}")

async def جيب_كل_الجروبات():
    if not supabase: return []
    try:
        r = supabase.table("جروبات").select("*").execute()
        return r.data or []
    except: return []

async def جيب_إحصائيات():
    if not supabase: return None
    try:
        م = supabase.table("مستخدمين").select("*", count="exact").execute()
        ح = supabase.table("تحذيرات").select("*").gte("عدد", 1).execute()
        return {"مستخدمين": م.count or 0, "محذورين": len(ح.data) if ح.data else 0}
    except: return None


# ==================== قوائم ====================
def القائمة_الرئيسية():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔨 حظر", callback_data="حظر"), InlineKeyboardButton("🔓 فك الحظر", callback_data="فك_حظر")],
        [InlineKeyboardButton("🔇 كتم", callback_data="كتم"), InlineKeyboardButton("🔊 فك الكتم", callback_data="فك_كتم")],
        [InlineKeyboardButton("⚠️ تحذير", callback_data="تحذير"), InlineKeyboardButton("🗑 مسح", callback_data="مسح")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="إحصائيات"), InlineKeyboardButton("📋 القوانين", callback_data="قوانين")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="مساعدة")],
    ])

def قائمة_التحكم():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات", callback_data="ctrl_إحصائيات"), InlineKeyboardButton("❓ سؤال الآن", callback_data="ctrl_سؤال")],
        [InlineKeyboardButton("⏹ وقف المعسكر", callback_data="ctrl_وقف"), InlineKeyboardButton("📋 القوانين", callback_data="ctrl_قوانين")],
        [InlineKeyboardButton("🔒 قفل الجروب", callback_data="ctrl_قفل"), InlineKeyboardButton("🔓 فتح الجروب", callback_data="ctrl_فتح")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="ctrl_رئيسية")],
    ])


# ==================== دوال مساعدة ====================
async def هو_ادمن(update, context):
    م = update.effective_user
    ش = update.effective_chat
    if ش.type == "private": return True
    ع = await context.bot.get_chat_member(ش.id, م.id)
    return ع.status in ["administrator", "creator"]

def فيه_كلمة_محظورة(نص):
    return any(ك in نص.lower() for ك in كلمات_محظورة)

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
                    "شرح": str(row[6]) if len(row) > 6 and row[6] else "",
                })
        return len(أسئلة_البوت)
    except Exception as e:
        logging.error(f"قراءة أسئلة: {e}")
        return 0


# ==================== دوال المعسكر ====================
async def بدء_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0: return
    info = context.job.data
    رسالة = (
        "🏕️ *معسكر أسئلة جديد!*\n\n"
        f"📚 *المادة:* {info['اسم_المادة']}\n"
        f"📝 *عدد الأسئلة:* {info['عدد_أسئلة']} سؤال\n"
        f"⏱️ *سؤال كل:* {info['كل_دقايق']} دقيقة\n"
        "🕐 *مدة الإجابة:* 10 دقائق لكل سؤال\n\n"
        "🤲 *دعاء طلب العلم:*\n"
        "اللهم علمنا ما ينفعنا، وانفعنا بما علمتنا،\n"
        "وزدنا علماً، وارزقنا فهماً وحفظاً\n\n"
        "يلا نذاكر! 💪🔥"
    )
    await context.bot.send_message(CHAT_ID, رسالة, parse_mode="Markdown")

async def نهاية_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0: return
    رسالة = (
        "🏆 *انتهى المعسكر!*\n\n"
        "بارك الله فيكم على المشاركة 🌟\n\n"
        "🤲 *دعاء ختم المذاكرة:*\n"
        "اللهم اجعل ما تعلمناه نافعاً، وثبّته في قلوبنا\n\n"
        "الحمد لله الذي بنعمته تتم الصالحات 🌹\n"
        "نراكم في المعسكر القادم إن شاء الله 💫"
    )
    await context.bot.send_message(CHAT_ID, رسالة, parse_mode="Markdown")

async def إرسال_تحفيز(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0: return
    await context.bot.send_message(CHAT_ID, random.choice(رسائل_تحفيزية), parse_mode="Markdown")

async def إرسال_ذكر(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0: return
    await context.bot.send_message(CHAT_ID, random.choice(أذكار), parse_mode="Markdown")

async def إرسال_سؤال(context: ContextTypes.DEFAULT_TYPE):
    global سؤال_حالي, index_سؤال, إحصائيات_معسكر
    if not أسئلة_البوت or CHAT_ID == 0: return
    if index_سؤال >= len(أسئلة_مخلوطة):
        for job in context.job_queue.get_jobs_by_name("أسئلة"):
            job.schedule_removal()
        context.job_queue.run_once(نهاية_المعسكر, 2, data={})
        return
    سؤال_حالي = أسئلة_مخلوطة[index_سؤال]
    index_سؤال += 1
    إحصائيات_معسكر["أسئلة_بُعتت"] += 1
    خيارات = [سؤال_حالي['أ'], سؤال_حالي['ب'], سؤال_حالي['ج'], سؤال_حالي['د']]
    حروف = ['أ', 'ب', 'ج', 'د']
    رقم = حروف.index(سؤال_حالي['إجابة'])
    شرح = f"✅ {سؤال_حالي['إجابة']}) {سؤال_حالي[سؤال_حالي['إجابة']]}"
    if سؤال_حالي.get('شرح'):
        شرح += f"\n\n💡 {سؤال_حالي['شرح']}"
    await context.bot.send_poll(
        chat_id=CHAT_ID,
        question=f"🧠 {سؤال_حالي['سؤال']}",
        options=خيارات,
        type="quiz",
        correct_option_id=رقم,
        is_anonymous=False,
        open_period=600,
        explanation=شرح,
    )


# ==================== Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    await سجل_مستخدم(م.id, م.first_name, م.username)
    if OWNER_ID != 0 and م.id != OWNER_ID:
        ي = f"@{م.username}" if م.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n\n👤 {م.first_name}\n🔗 {ي}\n🆔 `{م.id}`", parse_mode="Markdown")
        except: pass
    await update.message.reply_text(
        "👋 *أهلاً! أنا بووووو*\n\n🔹 إدارة الأعضاء\n🔹 ذكاء اصطناعي بالمصري\n🔹 معسكرات أسئلة\n\nاختار من القائمة 👇",
        parse_mode="Markdown", reply_markup=القائمة_الرئيسية()
    )

async def لوحة_التحكم(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    if م.id != OWNER_ID:
        await update.message.reply_text("❌ للأدمن فقط.")
        return
    إحصاء = await جيب_إحصائيات()
    await update.message.reply_text(
        f"🎛 *لوحة التحكم*\n\n👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n📚 الأسئلة: {len(أسئلة_البوت)}\n✅ أسئلة اتبعتت: {إحصائيات_معسكر['أسئلة_بُعتت']}",
        parse_mode="Markdown", reply_markup=قائمة_التحكم()
    )

async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ن = update.chat_member
    ع = ن.new_chat_member.user
    ش = update.effective_chat
    if ن.new_chat_member.user.id == (await context.bot.get_me()).id:
        await سجل_جروب(ش.id, ش.title or "جروب")
        if OWNER_ID != 0:
            try:
                await context.bot.send_message(OWNER_ID, f"➕ *البوت اتضاف لجروب جديد!*\n\n📛 {ش.title}\n🆔 `{ش.id}`", parse_mode="Markdown")
            except: pass
        return
    if ن.new_chat_member.status == "member":
        await سجل_مستخدم(ع.id, ع.first_name, ع.username)
        await context.bot.send_message(ش.id, f"👋 *أهلاً {ع.first_name}!*\n\nيسعدنا انضمامك 🎉\n\n{قوانين_الجروب}", parse_mode="Markdown")

async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data

    if بيانات.startswith("ctrl_"):
        أمر = بيانات.replace("ctrl_", "")
        if أمر == "إحصائيات":
            إحصاء = await جيب_إحصائيات()
            await query.edit_message_text(
                f"📊 *الإحصائيات*\n\n👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n📚 الأسئلة: {len(أسئلة_البوت)}\n✅ أسئلة بُعتت: {إحصائيات_معسكر['أسئلة_بُعتت']}",
                parse_mode="Markdown", reply_markup=قائمة_التحكم()
            )
        elif أمر == "سؤال":
            if not أسئلة_البوت:
                await query.answer("❌ ارفع ملف الأسئلة!", show_alert=True)
            else:
                await إرسال_سؤال(context)
                await query.answer("✅ تم إرسال سؤال!", show_alert=True)
        elif أمر == "وقف":
            for job in context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("تحفيز") + context.job_queue.get_jobs_by_name("أذكار"):
                job.schedule_removal()
            context.job_queue.run_once(نهاية_المعسكر, 2, data={})
            await query.answer("✅ تم إنهاء المعسكر.", show_alert=True)
        elif أمر == "قوانين":
            await query.edit_message_text(قوانين_الجروب, parse_mode="Markdown", reply_markup=قائمة_التحكم())
        elif أمر == "قفل":
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=False, can_send_polls=False, can_send_other_messages=False, can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                await context.bot.send_message(CHAT_ID, "🔒 *تم قفل الجروب*", parse_mode="Markdown")
                await query.answer("✅ تم قفل الجروب.", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ {e}", show_alert=True)
        elif أمر == "فتح":
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False))
                await context.bot.send_message(CHAT_ID, "🔓 *تم فتح الجروب*", parse_mode="Markdown")
                await query.answer("✅ تم فتح الجروب.", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ {e}", show_alert=True)
        elif أمر == "رئيسية":
            await query.edit_message_text("اختار من القائمة 👇", reply_markup=القائمة_الرئيسية())
        return

    if بيانات == "إحصائيات":
        إحصاء = await جيب_إحصائيات()
        await query.edit_message_text(
            f"📊 *إحصائيات*\n\n👥 {إحصاء['مستخدمين'] if إحصاء else 0}\n⚠️ {إحصاء['محذورين'] if إحصاء else 0}\n📚 {len(أسئلة_البوت)}",
            parse_mode="Markdown", reply_markup=القائمة_الرئيسية()
        )
        return

    نصوص = {
        "مساعدة": "📖 *دليل الاستخدام*\n\nرد على رسالة العضو واكتب:\nحظر | فك حظر | كتم | فك كتم | تحذير | مسح\n\n📚 ابعت ملف Excel للأسئلة\n🎛 /ctrl للوحة التحكم",
        "قوانين": قوانين_الجروب,
        "حظر": "🔨 رد على رسالة العضو واكتب: *حظر*",
        "فك_حظر": "🔓 رد على رسالة العضو واكتب: *فك حظر*",
        "كتم": "🔇 رد على رسالة العضو واكتب: *كتم*",
        "فك_كتم": "🔊 رد على رسالة العضو واكتب: *فك كتم*",
        "تحذير": "⚠️ رد على رسالة العضو واكتب: *تحذير*\n3 تحذيرات = حظر تلقائي",
        "مسح": "🗑 رد على الرسالة واكتب: *مسح*",
    }
    await query.edit_message_text(نصوص.get(بيانات, "❓"), parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def معالج_الملفات(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    if م.id != OWNER_ID:
        await update.message.reply_text("❌ للأدمن فقط.")
        return
    document = update.message.document
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ ارفع ملف .xlsx فقط.")
        return
    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    عدد = قراءة_أسئلة(bytes(file_bytes))
    if عدد > 0:
        context.user_data['عدد_أسئلة'] = عدد
        context.user_data['انتظر_مادة'] = True
        await update.message.reply_text(f"✅ تم رفع *{عدد}* سؤال!\n\n📚 ما اسم المادة؟", parse_mode="Markdown")
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
    م = update.effective_user

    if في_الخاص and م.id == OWNER_ID:

        if context.user_data.get('انتظر_مادة'):
            معسكر_info['اسم_المادة'] = نص
            context.user_data['انتظر_مادة'] = False
            context.user_data['انتظر_وقت'] = True
            await update.message.reply_text(f"✅ المادة: *{نص}*\n\n⏱️ كل كام دقيقة تبعت سؤال؟", parse_mode="Markdown")
            return

        if context.user_data.get('انتظر_وقت') and نص.isdigit():
            global index_سؤال, أسئلة_مخلوطة, إحصائيات_معسكر
            دقائق = int(نص)
            معسكر_info['كل_دقايق'] = دقائق
            context.user_data['انتظر_وقت'] = False
            عدد = context.user_data.get('عدد_أسئلة', len(أسئلة_البوت))

            for job in context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("تحفيز") + context.job_queue.get_jobs_by_name("أذكار"):
                job.schedule_removal()

            أسئلة_مخلوطة = أسئلة_البوت.copy()
            random.shuffle(أسئلة_مخلوطة)
            index_سؤال = 0
            إحصائيات_معسكر = {"أسئلة_بُعتت": 0}

            context.job_queue.run_once(بدء_المعسكر, 5, data={'اسم_المادة': معسكر_info['اسم_المادة'], 'عدد_أسئلة': عدد, 'كل_دقايق': دقائق})
            context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=15, name="أسئلة")
            context.job_queue.run_repeating(إرسال_تحفيز, interval=دقائق * 60 * 2, first=دقائق * 60, name="تحفيز")
            context.job_queue.run_repeating(إرسال_ذكر, interval=15 * 60, first=15 * 60, name="أذكار")

            await update.message.reply_text(
                f"🏕️ *المعسكر جاهز!*\n\n📚 {معسكر_info['اسم_المادة']}\n⏱️ سؤال كل {دقائق} دقيقة\n🤲 أذكار كل 15 دقيقة\n\nسيبدأ خلال ثواني 🚀",
                parse_mode="Markdown"
            )
            return

        if نص.startswith("بعت للكل:"):
            رسالة_عامة = نص.replace("بعت للكل:", "").strip()
            if not رسالة_عامة:
                await update.message.reply_text("❌ اكتب الرسالة بعد : مثلاً:\nبعت للكل: أهلاً بالجميع")
                return
            if not supabase:
                await update.message.reply_text("❌ Supabase مش شغال")
                return
            await update.message.reply_text("⏳ جاري الإرسال...")
            try:
                users = supabase.table("مستخدمين").select("user_id").execute()
                نجح = 0
                فشل = 0
                for user in (users.data or []):
                    try:
                        await context.bot.send_message(user["user_id"], رسالة_عامة, parse_mode="Markdown")
                        نجح += 1
                    except:
                        فشل += 1
                await update.message.reply_text(f"✅ تم الإرسال!\n\n📤 نجح: {نجح}\n❌ فشل: {فشل}")
            except Exception as e:
                await update.message.reply_text(f"❌ خطأ: {e}")
            return

        if نص in ["جروباتي", "جروبات البوت"]:
            جروبات = await جيب_كل_الجروبات()
            if not جروبات:
                await update.message.reply_text("❌ البوت مش في أي جروب دلوقتي")
                return
            نص_جروبات = "📋 *الجروبات اللي البوت فيها:*\n\n"
            for i, ج in enumerate(جروبات, 1):
                نص_جروبات += f"{i}. {ج.get('اسم', 'بدون اسم')} — `{ج['chat_id']}`\n"
            await update.message.reply_text(نص_جروبات, parse_mode="Markdown")
            return

        if نص in ["إحصائيات المعسكر", "كام سؤال", "احصائيات"]:
            متبقي = len(أسئلة_مخلوطة) - index_سؤال
            await update.message.reply_text(
                f"📊 *إحصائيات المعسكر*\n\n"
                f"✅ أسئلة اتبعتت: {إحصائيات_معسكر['أسئلة_بُعتت']}\n"
                f"📚 إجمالي الأسئلة: {len(أسئلة_مخلوطة)}\n"
                f"⏳ متبقي: {متبقي} سؤال",
                parse_mode="Markdown"
            )
            return

        match = re.match(r'ابعت كل (\d+) دقيقة', نص)
        if match:
            دقائق = int(match.group(1))
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            for job in context.job_queue.get_jobs_by_name("أسئلة"):
                job.schedule_removal()
            context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=10, name="أسئلة")
            await update.message.reply_text(f"✅ هيبعت سؤال كل *{دقائق}* دقيقة", parse_mode="Markdown")
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
            await update.message.reply_text(f"✅ هيبعت سؤال الساعة *{ساعة}*", parse_mode="Markdown")
            return

        if نص in ["وقف", "وقف الأسئلة", "إنهاء المعسكر", "stop"]:
            for job in context.job_queue.get_jobs_by_name("أسئلة") + context.job_queue.get_jobs_by_name("أسئلة_يومية") + context.job_queue.get_jobs_by_name("تحفيز") + context.job_queue.get_jobs_by_name("أذكار"):
                job.schedule_removal()
            context.job_queue.run_once(نهاية_المعسكر, 2, data={})
            await update.message.reply_text("✅ تم إنهاء المعسكر.")
            return

        if نص in ["ابعت سؤال", "سؤال الآن"]:
            if not أسئلة_البوت:
                await update.message.reply_text("❌ ارفع ملف الأسئلة الأول!")
                return
            await إرسال_سؤال(context)
            await update.message.reply_text("✅ تم إرسال سؤال!")
            return

        if نص in ["اقفل الجروب", "قفل الجروب"]:
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=False, can_send_polls=False, can_send_other_messages=False, can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                await context.bot.send_message(CHAT_ID, "🔒 *تم قفل الجروب*", parse_mode="Markdown")
                await update.message.reply_text("✅ تم قفل الجروب.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        if نص in ["افتح الجروب", "فتح الجروب"]:
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False))
                await context.bot.send_message(CHAT_ID, "🔓 *تم فتح الجروب*", parse_mode="Markdown")
                await update.message.reply_text("✅ تم فتح الجروب.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص):
            try:
                await update.message.delete()
                ع = await جيب_تحذيرات(update.effective_chat.id, م.id)
                ج = ع + 1
                await حدث_تحذيرات(update.effective_chat.id, م.id, ج)
                if ج >= 3:
                    await context.bot.ban_chat_member(update.effective_chat.id, م.id)
                    await حدث_تحذيرات(update.effective_chat.id, م.id, 0)
                    await context.bot.send_message(update.effective_chat.id, f"🚫 تم حظر {م.first_name} تلقائياً!")
                else:
                    await context.bot.send_message(update.effective_chat.id, f"⚠️ {م.first_name} تحذير {ج}/3")
            except Exception as e:
                logging.error(f"فلتر: {e}")
            return
        if فيه_رابط(نص):
            try:
                await update.message.delete()
                await context.bot.send_message(update.effective_chat.id, f"🔗 {م.first_name} ممنوع نشر الروابط!")
            except: pass
            return

    if رد_على and await هو_ادمن(update, context):
        ع = رد_على.from_user
        if نص == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, ع.id)
                await update.message.reply_text(f"🔨 تم حظر {ع.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, ع.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {ع.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, ع.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {ع.first_name}.")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "فك كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, ع.id, permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=True, can_pin_messages=False))
                await update.message.reply_text(f"🔊 تم فك كتم {ع.first_name}.")
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
            ت = await جيب_تحذيرات(update.effective_chat.id, ع.id)
            ج = ت + 1
            await حدث_تحذيرات(update.effective_chat.id, ع.id, ج)
            if ج >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, ع.id)
                    await حدث_تحذيرات(update.effective_chat.id, ع.id, 0)
                    await update.message.reply_text(f"🚫 تم حظر {ع.first_name} بعد 3 تحذيرات!")
                except Exception as e:
                    await update.message.reply_text(f"❌ {e}")
            else:
                await update.message.reply_text(f"⚠️ تحذير {ج}/3 لـ {ع.first_name}")
            return

    if نص in ["القوانين", "قوانين", "rules"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return

    if نص == "chat_id" and await هو_ادمن(update, context):
        await update.message.reply_text(f"🆔 Chat ID: `{update.effective_chat.id}`", parse_mode="Markdown")
        return

    اتذكر = اسم_البوت.lower() in نص.lower()
    فيه_سؤال = "؟" in نص or "?" in نص

    if في_الخاص or اتذكر or فيه_سؤال:
        س = نص.replace(اسم_البوت, "").strip()
        if not س: return
        try:
            await context.bot.send_chat_action(update.effective_chat.id, "typing")
            رد = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": f"أنت مساعد ذكي اسمك بووووو، صنعك {اسم_الصانع}. لازم تتكلم بالعامية المصرية دايماً، ردودك خفيفة وودودة ومفيدة. لو حد سألك مين صنعك قوله {اسم_الصانع}. لو في سؤال دراسي جاوبه بدقة بالعامية المصرية."},
                    {"role": "user", "content": س}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")


async def إرسال_رسالة_مجدولة(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID == 0: return
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
        for ر in رسائل_مجدولة:
            تطبيق.job_queue.run_daily(إرسال_رسالة_مجدولة, time=ر["الوقت"], data=ر["الرسالة"])
    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
