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
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

اسم_الصانع = "Moaz{@Almoo5m}"

# بيانات المعسكرات لكل جروب
معسكرات = {}  # {chat_id: {...}}

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
    "1️⃣ الاحترام المتبادل\n"
    "2️⃣ ممنوع السب والشتيمة\n"
    "3️⃣ ممنوع الاعلانات والسبام\n"
    "4️⃣ ممنوع نشر روابط بدون اذن\n"
    "5️⃣ الالتزام بموضوع الجروب\n\n"
    "مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي."
)


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

async def سجل_جروب(chat_id, اسم, owner_id):
    if not supabase: return
    try:
        e = supabase.table("جروبات").select("id").eq("chat_id", chat_id).execute()
        if not e.data:
            supabase.table("جروبات").insert({"chat_id": chat_id, "اسم": اسم, "owner_id": owner_id}).execute()
        else:
            supabase.table("جروبات").update({"اسم": اسم}).eq("chat_id", chat_id).execute()
    except Exception as ex:
        logging.error(f"سجل_جروب: {ex}")

async def جيب_owner_id(chat_id):
    if not supabase: return None
    try:
        r = supabase.table("جروبات").select("owner_id").eq("chat_id", chat_id).execute()
        return r.data[0]["owner_id"] if r.data else None
    except: return None

async def ai_مفعل_للجروب(chat_id):
    if not supabase: return False
    try:
        owner = await جيب_owner_id(chat_id)
        if not owner: return False
        r = supabase.table("اشتراكات").select("ai_مفعل").eq("user_id", owner).eq("chat_id", chat_id).execute()
        return r.data[0]["ai_مفعل"] if r.data else False
    except: return False

async def جيب_طلبات_الاشتراك():
    if not supabase: return []
    try:
        r = supabase.table("اشتراكات").select("*").eq("ai_مفعل", False).execute()
        return r.data or []
    except: return []

async def فعّل_ai(user_id, chat_id):
    if not supabase: return False
    try:
        e = supabase.table("اشتراكات").select("id").eq("user_id", user_id).eq("chat_id", chat_id).execute()
        if e.data:
            supabase.table("اشتراكات").update({"ai_مفعل": True}).eq("user_id", user_id).eq("chat_id", chat_id).execute()
        else:
            supabase.table("اشتراكات").insert({"user_id": user_id, "chat_id": chat_id, "ai_مفعل": True}).execute()
        return True
    except: return False

async def وقف_ai(user_id, chat_id):
    if not supabase: return False
    try:
        supabase.table("اشتراكات").update({"ai_مفعل": False}).eq("user_id", user_id).eq("chat_id", chat_id).execute()
        return True
    except: return False

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
        ج = supabase.table("جروبات").select("*", count="exact").execute()
        اش = supabase.table("اشتراكات").select("*").eq("ai_مفعل", True).execute()
        return {
            "مستخدمين": م.count or 0,
            "محذورين": len(ح.data) if ح.data else 0,
            "جروبات": ج.count or 0,
            "مشتركين_ai": len(اش.data) if اش.data else 0,
        }
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

def قائمة_سوبر_أدمن():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات كاملة", callback_data="super_إحصائيات")],
        [InlineKeyboardButton("🏘 الجروبات", callback_data="super_جروبات")],
        [InlineKeyboardButton("🔔 طلبات AI", callback_data="super_طلبات")],
        [InlineKeyboardButton("📢 إعلان للكل", callback_data="super_إعلان")],
    ])

def قائمة_تحكم_جروب(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ سؤال الآن", callback_data=f"grp_سؤال_{chat_id}"), InlineKeyboardButton("⏹ وقف المعسكر", callback_data=f"grp_وقف_{chat_id}")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data=f"grp_إحصائيات_{chat_id}"), InlineKeyboardButton("📋 القوانين", callback_data=f"grp_قوانين_{chat_id}")],
        [InlineKeyboardButton("🔒 قفل الجروب", callback_data=f"grp_قفل_{chat_id}"), InlineKeyboardButton("🔓 فتح الجروب", callback_data=f"grp_فتح_{chat_id}")],
        [InlineKeyboardButton("🤖 اشتراك AI 💎", callback_data=f"grp_ai_{chat_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="رئيسية")],
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
    أسئلة = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and len(row) >= 6 and all(row[:6]):
                أسئلة.append({
                    "سؤال": str(row[0]), "إجابة": str(row[1]),
                    "أ": str(row[2]), "ب": str(row[3]), "ج": str(row[4]), "د": str(row[5]),
                    "شرح": str(row[6]) if len(row) > 6 and row[6] else "",
                })
        return أسئلة
    except Exception as e:
        logging.error(f"قراءة أسئلة: {e}")
        return []

def جيب_بيانات_جروب(chat_id):
    if chat_id not in معسكرات:
        معسكرات[chat_id] = {
            "أسئلة": [], "مخلوطة": [], "index": 0,
            "إحصائيات": {"أسئلة_بُعتت": 0},
            "info": {"اسم_المادة": "", "كل_دقايق": 1},
        }
    return معسكرات[chat_id]


# ==================== دوال المعسكر ====================
async def بدء_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    chat_id = data["chat_id"]
    رسالة = (
        "🏕️ *معسكر أسئلة جديد!*\n\n"
        f"📚 *المادة:* {data['اسم_المادة']}\n"
        f"📝 *عدد الأسئلة:* {data['عدد_أسئلة']} سؤال\n"
        f"⏱️ *سؤال كل:* {data['كل_دقايق']} دقيقة\n"
        "🕐 *مدة الإجابة:* 10 دقائق لكل سؤال\n\n"
        "🤲 *دعاء طلب العلم:*\n"
        "اللهم علمنا ما ينفعنا، وانفعنا بما علمتنا،\n"
        "وزدنا علماً، وارزقنا فهماً وحفظاً\n\n"
        "يلا نذاكر! 💪🔥"
    )
    await context.bot.send_message(chat_id, رسالة, parse_mode="Markdown")

async def نهاية_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    await context.bot.send_message(
        chat_id,
        "🏆 *انتهى المعسكر!*\n\nبارك الله فيكم 🌟\n\n"
        "🤲 اللهم اجعل ما تعلمناه نافعاً\n\n"
        "الحمد لله الذي بنعمته تتم الصالحات 🌹",
        parse_mode="Markdown"
    )

async def إرسال_تحفيز(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.data["chat_id"], random.choice(رسائل_تحفيزية), parse_mode="Markdown")

async def إرسال_ذكر(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.data["chat_id"], random.choice(أذكار), parse_mode="Markdown")

async def إرسال_سؤال(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    بيانات = جيب_بيانات_جروب(chat_id)
    if not بيانات["أسئلة"]: return
    if بيانات["index"] >= len(بيانات["مخلوطة"]):
        for job in context.job_queue.get_jobs_by_name(f"أسئلة_{chat_id}"):
            job.schedule_removal()
        context.job_queue.run_once(نهاية_المعسكر, 2, data={"chat_id": chat_id}, name=f"نهاية_{chat_id}")
        return
    سؤال = بيانات["مخلوطة"][بيانات["index"]]
    بيانات["index"] += 1
    بيانات["إحصائيات"]["أسئلة_بُعتت"] += 1
    خيارات = [سؤال['أ'], سؤال['ب'], سؤال['ج'], سؤال['د']]
    رقم = ['أ', 'ب', 'ج', 'د'].index(سؤال['إجابة'])
    شرح = f"✅ {سؤال['إجابة']}) {سؤال[سؤال['إجابة']]}"
    if سؤال.get('شرح'):
        شرح += f"\n\n💡 {سؤال['شرح']}"
    await context.bot.send_poll(
        chat_id=chat_id,
        question=f"🧠 {سؤال['سؤال']}",
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
    if م.id == OWNER_ID:
        إحصاء = await جيب_إحصائيات()
        await update.message.reply_text(
            f"👑 *أهلاً يا Moaz!*\n\n"
            f"👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n"
            f"🏘 الجروبات: {إحصاء['جروبات'] if إحصاء else 0}\n"
            f"🤖 مشتركين AI: {إحصاء['مشتركين_ai'] if إحصاء else 0}",
            parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
        )
        return
    if OWNER_ID != 0:
        ي = f"@{م.username}" if م.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n\n👤 {م.first_name}\n🔗 {ي}\n🆔 `{م.id}`", parse_mode="Markdown")
        except: pass
    await update.message.reply_text(
        "👋 *أهلاً! أنا بووووو*\n\n"
        "🔹 إدارة الأعضاء — مجاناً\n"
        "🔹 فلتر تلقائي — مجاناً\n"
        "🔹 معسكرات أسئلة — مجاناً\n"
        "🤖 ذكاء اصطناعي — بريميوم 💎\n\n"
        "ضيفني في جروبك واكتب /ctrl 👇",
        parse_mode="Markdown", reply_markup=القائمة_الرئيسية()
    )

async def ctrl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    ش = update.effective_chat
    if م.id == OWNER_ID and ش.type == "private":
        إحصاء = await جيب_إحصائيات()
        await update.message.reply_text(
            f"👑 *لوحة السوبر أدمن*\n\n"
            f"👥 {إحصاء['مستخدمين'] if إحصاء else 0} مستخدم\n"
            f"🏘 {إحصاء['جروبات'] if إحصاء else 0} جروب\n"
            f"🤖 {إحصاء['مشتركين_ai'] if إحصاء else 0} مشترك AI",
            parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
        )
        return
    if ش.type == "private":
        await update.message.reply_text("❌ الأمر ده بيشتغل في الجروب بس.")
        return
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ للأدمن فقط.")
        return
    await update.message.reply_text(
        f"🎛 *لوحة تحكم الجروب*\n📛 {ش.title}\n\nارفع ملف Excel للأسئلة هنا 👇",
        parse_mode="Markdown",
        reply_markup=قائمة_تحكم_جروب(ش.id)
    )

async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ن = update.chat_member
    ع = ن.new_chat_member.user
    ش = update.effective_chat
    بوت = await context.bot.get_me()

    if ع.id == بوت.id:
        try:
            أعضاء = await context.bot.get_chat_administrators(ش.id)
            owner_id = next((a.user.id for a in أعضاء if a.status == "creator"), None)
        except:
            owner_id = None
        await سجل_جروب(ش.id, ش.title or "جروب", owner_id)
        if OWNER_ID != 0:
            try:
                await context.bot.send_message(
                    OWNER_ID,
                    f"➕ *جروب جديد!*\n\n📛 {ش.title}\n🆔 `{ش.id}`\n👤 الأونر: `{owner_id}`",
                    parse_mode="Markdown"
                )
            except: pass
        await context.bot.send_message(
            ش.id,
            "👋 *أهلاً! أنا بووووو*\n\n🔹 إدارة الأعضاء\n🔹 فلتر تلقائي\n🔹 معسكرات أسئلة\n\nالأدمن يكتب /ctrl 🎛",
            parse_mode="Markdown"
        )
        return

    if ن.new_chat_member.status == "member":
        await سجل_مستخدم(ع.id, ع.first_name, ع.username)
        if OWNER_ID != 0:
            try:
                ي = f"@{ع.username}" if ع.username else "مفيش يوزرنيم"
                await context.bot.send_message(
                    OWNER_ID,
                    f"👤 *عضو جديد في {ش.title}*\n{ع.first_name} — {ي}\n🆔 `{ع.id}`",
                    parse_mode="Markdown"
                )
            except: pass
        await context.bot.send_message(
            ش.id,
            f"👋 *أهلاً {ع.first_name}!*\n\nيسعدنا انضمامك 🎉\n\n{قوانين_الجروب}",
            parse_mode="Markdown"
        )

async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    بيانات = query.data
    م = query.from_user

    # ===== سوبر أدمن =====
    if بيانات.startswith("super_") and م.id == OWNER_ID:
        أمر = بيانات.replace("super_", "")
        if أمر == "إحصائيات":
            إحصاء = await جيب_إحصائيات()
            await query.edit_message_text(
                f"📊 *إحصائيات كاملة*\n\n"
                f"👥 المستخدمين: {إحصاء['مستخدمين'] if إحصاء else 0}\n"
                f"🏘 الجروبات: {إحصاء['جروبات'] if إحصاء else 0}\n"
                f"⚠️ المحذّرين: {إحصاء['محذورين'] if إحصاء else 0}\n"
                f"🤖 مشتركين AI: {إحصاء['مشتركين_ai'] if إحصاء else 0}",
                parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
            )
        elif أمر == "جروبات":
            جروبات = await جيب_كل_الجروبات()
            if not جروبات:
                await query.answer("❌ مفيش جروبات", show_alert=True)
                return
            نص = "🏘 *الجروبات:*\n\n"
            for i, ج in enumerate(جروبات, 1):
                نص += f"{i}. {ج.get('اسم', '؟')} — `{ج['chat_id']}`\n"
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن())
        elif أمر == "طلبات":
            طلبات = await جيب_طلبات_الاشتراك()
            if not طلبات:
                await query.answer("✅ مفيش طلبات جديدة", show_alert=True)
                return
            نص = "🔔 *طلبات تفعيل AI:*\n\n"
            أزرار = []
            for ط in طلبات:
                نص += f"👤 `{ط['user_id']}` — جروب `{ط['chat_id']}`\n"
                أزرار.append([
                    InlineKeyboardButton(f"✅ فعّل", callback_data=f"activate_{ط['user_id']}_{ط['chat_id']}"),
                    InlineKeyboardButton(f"❌ ارفض", callback_data=f"reject_{ط['user_id']}_{ط['chat_id']}"),
                ])
            أزرار.append([InlineKeyboardButton("🔙 رجوع", callback_data="super_رئيسية")])
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(أزرار))
        elif أمر == "إعلان":
            context.user_data["انتظر_إعلان"] = True
            await query.edit_message_text(
                "📢 *اكتب نص الإعلان:*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="super_رئيسية")]])
            )
        elif أمر == "رئيسية":
            إحصاء = await جيب_إحصائيات()
            await query.edit_message_text(
                f"👑 *لوحة السوبر أدمن*\n\n👥 {إحصاء['مستخدمين'] if إحصاء else 0} مستخدم\n🏘 {إحصاء['جروبات'] if إحصاء else 0} جروب\n🤖 {إحصاء['مشتركين_ai'] if إحصاء else 0} مشترك AI",
                parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
            )
        return

    # ===== تفعيل / رفض AI =====
    if بيانات.startswith("activate_") and م.id == OWNER_ID:
        parts = بيانات.split("_")
        user_id, chat_id = int(parts[1]), int(parts[2])
        if await فعّل_ai(user_id, chat_id):
            try:
                await context.bot.send_message(user_id, "🎉 *تم تفعيل AI في جروبك!*\n\nالأعضاء يقدروا يستخدموا الذكاء الاصطناعي دلوقتي 🤖", parse_mode="Markdown")
            except: pass
            await query.answer("✅ تم التفعيل!", show_alert=True)
        return

    if بيانات.startswith("reject_") and م.id == OWNER_ID:
        parts = بيانات.split("_")
        user_id = int(parts[1])
        try:
            await context.bot.send_message(user_id, "❌ *تم رفض طلب الاشتراك*\n\nللاستفسار تواصل مع الدعم.", parse_mode="Markdown")
        except: pass
        await query.answer("تم الرفض", show_alert=True)
        return

    # ===== تحكم الجروب =====
    if بيانات.startswith("grp_"):
        parts = بيانات.replace("grp_", "").split("_")
        أمر = parts[0]
        chat_id = int(parts[1]) if len(parts) > 1 else None
        if not chat_id: return
        try:
            عضو = await context.bot.get_chat_member(chat_id, م.id)
            if عضو.status not in ["administrator", "creator"] and م.id != OWNER_ID:
                await query.answer("❌ مش أدمن في الجروب ده!", show_alert=True)
                return
        except:
            if م.id != OWNER_ID:
                await query.answer("❌ مش قادر أتحقق", show_alert=True)
                return

        بيانات_جروب = جيب_بيانات_جروب(chat_id)

        if أمر == "إحصائيات":
            await query.edit_message_text(
                f"📊 *إحصائيات المعسكر*\n\n✅ بُعتت: {بيانات_جروب['إحصائيات']['أسئلة_بُعتت']}\n📚 إجمالي: {len(بيانات_جروب['مخلوطة'])}\n⏳ متبقي: {len(بيانات_جروب['مخلوطة']) - بيانات_جروب['index']}",
                parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(chat_id)
            )
        elif أمر == "سؤال":
            if not بيانات_جروب["أسئلة"]:
                await query.answer("❌ ارفع ملف الأسئلة الأول!", show_alert=True)
            else:
                context.job_queue.run_once(إرسال_سؤال, 1, data={"chat_id": chat_id}, name=f"فوري_{chat_id}")
                await query.answer("✅ تم إرسال سؤال!", show_alert=True)
        elif أمر == "وقف":
            for job in (context.job_queue.get_jobs_by_name(f"أسئلة_{chat_id}") + context.job_queue.get_jobs_by_name(f"تحفيز_{chat_id}") + context.job_queue.get_jobs_by_name(f"أذكار_{chat_id}")):
                job.schedule_removal()
            context.job_queue.run_once(نهاية_المعسكر, 2, data={"chat_id": chat_id}, name=f"نهاية_{chat_id}")
            await query.answer("✅ تم إنهاء المعسكر.", show_alert=True)
        elif أمر == "قوانين":
            await context.bot.send_message(chat_id, قوانين_الجروب, parse_mode="Markdown")
            await query.answer("✅ تم الإرسال", show_alert=True)
        elif أمر == "قفل":
            try:
                await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
                await context.bot.send_message(chat_id, "🔒 *تم قفل الجروب*", parse_mode="Markdown")
                await query.answer("✅ تم القفل.", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ {e}", show_alert=True)
        elif أمر == "فتح":
            try:
                await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_invite_users=True))
                await context.bot.send_message(chat_id, "🔓 *تم فتح الجروب*", parse_mode="Markdown")
                await query.answer("✅ تم الفتح.", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ {e}", show_alert=True)
        elif أمر == "ai":
            مفعل = await ai_مفعل_للجروب(chat_id)
            if مفعل:
                await query.edit_message_text("🤖 *AI مفعّل في جروبك!*\n\nالأعضاء يقدروا يسألوا البوت أي سؤال.", parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(chat_id))
            else:
                if supabase:
                    try:
                        e = supabase.table("اشتراكات").select("id").eq("user_id", م.id).eq("chat_id", chat_id).execute()
                        if not e.data:
                            supabase.table("اشتراكات").insert({"user_id": م.id, "chat_id": chat_id, "الاسم": م.first_name, "ai_مفعل": False}).execute()
                    except: pass
                try:
                    await context.bot.send_message(
                        OWNER_ID,
                        f"💰 *طلب اشتراك AI!*\n\n👤 {م.first_name}\n🆔 `{م.id}`\n🏘 جروب: `{chat_id}`",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("✅ فعّل", callback_data=f"activate_{م.id}_{chat_id}"),
                            InlineKeyboardButton("❌ ارفض", callback_data=f"reject_{م.id}_{chat_id}"),
                        ]])
                    )
                except: pass
                await query.edit_message_text(
                    "🤖 *اشتراك الذكاء الاصطناعي*\n\n"
                    "للاشتراك:\n"
                    "1️⃣ ابعت المبلغ على فودافون كاش\n"
                    "2️⃣ ابعت إيصال الدفع للأدمن\n"
                    "3️⃣ سيتم التفعيل خلال ساعة\n\n"
                    "📱 *رقم فودافون كاش:* اضف رقمك هنا\n\n"
                    "✅ تم إرسال طلبك للأدمن!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=f"grp_إحصائيات_{chat_id}")]])
                )
        return

    # ===== قائمة عامة =====
    if بيانات == "رئيسية":
        await query.edit_message_text("اختار من القائمة 👇", reply_markup=القائمة_الرئيسية())
        return

    if بيانات == "إحصائيات":
        إحصاء = await جيب_إحصائيات()
        await query.edit_message_text(
            f"📊 *إحصائيات*\n\n👥 {إحصاء['مستخدمين'] if إحصاء else 0} مستخدم\n🏘 {إحصاء['جروبات'] if إحصاء else 0} جروب",
            parse_mode="Markdown", reply_markup=القائمة_الرئيسية()
        )
        return

    نصوص = {
        "مساعدة": "📖 *دليل الاستخدام*\n\nرد على رسالة العضو واكتب:\nحظر | فك حظر | كتم | فك كتم | تحذير | مسح\n\n📚 ارفع ملف Excel في الجروب للأسئلة\n🎛 /ctrl للوحة التحكم",
        "قوانين": قوانين_الجروب,
        "حظر": "🔨 رد على رسالة العضو واكتب: *حظر*",
        "فك_حظر": "🔓 رد على رسالة العضو واكتب: *فك حظر*",
        "كتم": "🔇 رد على رسالة العضو واكتب: *كتم*",
        "فك_كتم": "🔊 رد على رسالة العضو واكتب: *فك كتم*",
        "تحذير": "⚠️ رد على رسالة العضو واكتب: *تحذير*\n3 تحذيرات = حظر تلقائي",
        "مسح": "🗑 رد على الرسالة واكتب: *مسح*",
    }
    if بيانات in نصوص:
        await query.edit_message_text(نصوص[بيانات], parse_mode="Markdown", reply_markup=القائمة_الرئيسية())


async def معالج_الملفات(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ش = update.effective_chat
    if not await هو_ادمن(update, context):
        await update.message.reply_text("❌ للأدمن فقط.")
        return
    document = update.message.document
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ ارفع ملف .xlsx فقط.")
        return
    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    أسئلة = قراءة_أسئلة(bytes(file_bytes))
    if أسئلة:
        بيانات_جروب = جيب_بيانات_جروب(ش.id)
        بيانات_جروب["أسئلة"] = أسئلة
        context.user_data['انتظر_مادة'] = True
        context.user_data['chat_id_أسئلة'] = ش.id
        await update.message.reply_text(f"✅ تم رفع *{len(أسئلة)}* سؤال!\n\n📚 ما اسم المادة؟", parse_mode="Markdown")
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
    ش = update.effective_chat

    # ===== السوبر أدمن في الخاص =====
    if في_الخاص and م.id == OWNER_ID:
        if context.user_data.get("انتظر_إعلان"):
            context.user_data["انتظر_إعلان"] = False
            await update.message.reply_text("⏳ جاري الإرسال...")
            try:
                users = supabase.table("مستخدمين").select("user_id").execute()
                نجح = فشل = 0
                for user in (users.data or []):
                    try:
                        await context.bot.send_message(user["user_id"], نص, parse_mode="Markdown")
                        نجح += 1
                    except:
                        فشل += 1
                await update.message.reply_text(f"✅ نجح: {نجح} | ❌ فشل: {فشل}", reply_markup=قائمة_سوبر_أدمن())
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return

        match = re.match(r'تفعيل (\d+) (-?\d+)', نص)
        if match:
            uid, cid = int(match.group(1)), int(match.group(2))
            if await فعّل_ai(uid, cid):
                try:
                    await context.bot.send_message(uid, "🎉 *تم تفعيل AI في جروبك!*", parse_mode="Markdown")
                except: pass
                await update.message.reply_text(f"✅ تم تفعيل AI للمستخدم {uid}")
            else:
                await update.message.reply_text("❌ فشل التفعيل")
            return

        match = re.match(r'وقف_ai (\d+) (-?\d+)', نص)
        if match:
            uid, cid = int(match.group(1)), int(match.group(2))
            await وقف_ai(uid, cid)
            await update.message.reply_text(f"✅ تم وقف AI للمستخدم {uid}")
            return

        if نص in ["جروبات", "جروبات البوت"]:
            جروبات = await جيب_كل_الجروبات()
            نص_ج = "🏘 *الجروبات:*\n\n" + "\n".join(f"{i}. {ج.get('اسم','؟')} — `{ج['chat_id']}`" for i, ج in enumerate(جروبات, 1)) if جروبات else "❌ مفيش جروبات"
            await update.message.reply_text(نص_ج, parse_mode="Markdown")
            return

    # ===== انتظار اسم المادة =====
    if context.user_data.get('انتظر_مادة') and await هو_ادمن(update, context):
        chat_id = context.user_data.get('chat_id_أسئلة', ش.id)
        جيب_بيانات_جروب(chat_id)["info"]["اسم_المادة"] = نص
        context.user_data['انتظر_مادة'] = False
        context.user_data['انتظر_وقت'] = True
        await update.message.reply_text(f"✅ المادة: *{نص}*\n\n⏱️ كل كام دقيقة تبعت سؤال؟", parse_mode="Markdown")
        return

    # ===== انتظار الوقت =====
    if context.user_data.get('انتظر_وقت') and نص.isdigit() and await هو_ادمن(update, context):
        chat_id = context.user_data.get('chat_id_أسئلة', ش.id)
        بيانات_جروب = جيب_بيانات_جروب(chat_id)
        دقائق = int(نص)
        بيانات_جروب["info"]["كل_دقايق"] = دقائق
        context.user_data['انتظر_وقت'] = False
        for job in (context.job_queue.get_jobs_by_name(f"أسئلة_{chat_id}") + context.job_queue.get_jobs_by_name(f"تحفيز_{chat_id}") + context.job_queue.get_jobs_by_name(f"أذكار_{chat_id}")):
            job.schedule_removal()
        بيانات_جروب["مخلوطة"] = بيانات_جروب["أسئلة"].copy()
        random.shuffle(بيانات_جروب["مخلوطة"])
        بيانات_جروب["index"] = 0
        بيانات_جروب["إحصائيات"] = {"أسئلة_بُعتت": 0}
        context.job_queue.run_once(بدء_المعسكر, 5, data={"chat_id": chat_id, "اسم_المادة": بيانات_جروب["info"]["اسم_المادة"], "عدد_أسئلة": len(بيانات_جروب["أسئلة"]), "كل_دقايق": دقائق}, name=f"بدء_{chat_id}")
        context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=15, data={"chat_id": chat_id}, name=f"أسئلة_{chat_id}")
        context.job_queue.run_repeating(إرسال_تحفيز, interval=دقائق * 60 * 2, first=دقائق * 60, data={"chat_id": chat_id}, name=f"تحفيز_{chat_id}")
        context.job_queue.run_repeating(إرسال_ذكر, interval=15 * 60, first=15 * 60, data={"chat_id": chat_id}, name=f"أذكار_{chat_id}")
        await update.message.reply_text(f"🏕️ *المعسكر جاهز!*\n\n📚 {بيانات_جروب['info']['اسم_المادة']}\n⏱️ سؤال كل {دقائق} دقيقة\n\nسيبدأ خلال ثواني 🚀", parse_mode="Markdown")
        return

    # ===== فلتر تلقائي =====
    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص):
            try:
                await update.message.delete()
                ت = await جيب_تحذيرات(ش.id, م.id)
                ج = ت + 1
                await حدث_تحذيرات(ش.id, م.id, ج)
                if ج >= 3:
                    await context.bot.ban_chat_member(ش.id, م.id)
                    await حدث_تحذيرات(ش.id, م.id, 0)
                    await context.bot.send_message(ش.id, f"🚫 تم حظر {م.first_name} تلقائياً!")
                    try: await context.bot.send_message(OWNER_ID, f"🚫 حظر تلقائي في {ش.title}\n👤 {م.first_name} `{م.id}`", parse_mode="Markdown")
                    except: pass
                else:
                    await context.bot.send_message(ش.id, f"⚠️ {م.first_name} تحذير {ج}/3")
            except Exception as e:
                logging.error(f"فلتر: {e}")
            return
        if فيه_رابط(نص):
            try:
                await update.message.delete()
                await context.bot.send_message(ش.id, f"🔗 {م.first_name} ممنوع نشر الروابط!")
            except: pass
            return

    # ===== أوامر الإدارة =====
    if رد_على and await هو_ادمن(update, context):
        ع = رد_على.from_user
        if نص == "حظر":
            try:
                await context.bot.ban_chat_member(ش.id, ع.id)
                await update.message.reply_text(f"🔨 تم حظر {ع.first_name}.")
            except Exception as e: await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "فك حظر":
            try:
                await context.bot.unban_chat_member(ش.id, ع.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {ع.first_name}.")
            except Exception as e: await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "كتم":
            try:
                await context.bot.restrict_chat_member(ش.id, ع.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {ع.first_name}.")
            except Exception as e: await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "فك كتم":
            try:
                await context.bot.restrict_chat_member(ش.id, ع.id, permissions=ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_invite_users=True))
                await update.message.reply_text(f"🔊 تم فك كتم {ع.first_name}.")
            except Exception as e: await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "مسح":
            try:
                await رد_على.delete()
                await update.message.delete()
            except Exception as e: await update.message.reply_text(f"❌ {e}")
            return
        elif نص == "تحذير":
            ت = await جيب_تحذيرات(ش.id, ع.id)
            ج = ت + 1
            await حدث_تحذيرات(ش.id, ع.id, ج)
            if ج >= 3:
                try:
                    await context.bot.ban_chat_member(ش.id, ع.id)
                    await حدث_تحذيرات(ش.id, ع.id, 0)
                    await update.message.reply_text(f"🚫 تم حظر {ع.first_name} بعد 3 تحذيرات!")
                except Exception as e: await update.message.reply_text(f"❌ {e}")
            else:
                await update.message.reply_text(f"⚠️ تحذير {ج}/3 لـ {ع.first_name}")
            return

    if نص in ["القوانين", "قوانين", "rules"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return

    if نص == "chat_id" and await هو_ادمن(update, context):
        await update.message.reply_text(f"🆔 Chat ID: `{ش.id}`", parse_mode="Markdown")
        return

    # ===== الذكاء الاصطناعي =====
    اتذكر = اسم_البوت.lower() in نص.lower()
    فيه_سؤال = "؟" in نص or "?" in نص

    if (في_الخاص or اتذكر or فيه_سؤال) and groq_client:
        if not في_الخاص and not await ai_مفعل_للجروب(ش.id):
            if اتذكر or فيه_سؤال:
                await update.message.reply_text(
                    "🤖 الذكاء الاصطناعي للمشتركين فقط.\nاكتب /ctrl واختار *اشتراك AI* 💎",
                    parse_mode="Markdown"
                )
            return
        س = نص.replace(اسم_البوت, "").strip()
        if not س: return
        try:
            await context.bot.send_chat_action(ش.id, "typing")
            رد = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": f"أنت مساعد ذكي اسمك بووووو، صنعك {اسم_الصانع}. لازم تتكلم بالعامية المصرية دايماً، ردودك خفيفة وودودة ومفيدة. لو حد سألك مين صنعك قوله {اسم_الصانع}."},
                    {"role": "user", "content": س}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")


def main():
    if not TOKEN:
        raise ValueError("مفيش TOKEN!")
    تطبيق = ApplicationBuilder().token(TOKEN).build()
    تطبيق.add_handler(CommandHandler("start", start))
    تطبيق.add_handler(CommandHandler("ctrl", ctrl))
    تطبيق.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    تطبيق.add_handler(CallbackQueryHandler(معالج_الأزرار))
    تطبيق.add_handler(MessageHandler(filters.Document.ALL, معالج_الملفات))
    تطبيق.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))
    print("✅ البوت شغال...")
    تطبيق.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
