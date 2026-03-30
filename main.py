import os, re, io, logging, random, asyncio, json
from datetime import datetime, timedelta
from groq import Groq
import openpyxl
from supabase import create_client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, ContextTypes, filters
)

# ==================== المتغيرات البيئية ====================
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

# ==================== تهيئة العملاء ====================
groq_client = Groq(api_key=GROQ_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==================== المتغيرات العامة ====================
اسم_الصانع = "Moaz"
أسئلة_البوت = []
سؤال_حالي = {}
index_سؤال = 0
أسئلة_مخلوطة = []
معسكر_نشط = False
إحصائيات_معسكر = {"أسئلة_بُعتت": 0, "إجابات_صحيحة": 0}

# ==================== النصوص ====================
رسائل_تحفيزية = [
    "💪 *استمر! كل سؤال بتجاوبه هو خطوة نحو النجاح!*\n✨ العلم نور والجهل ظلام",
    "🔥 *أنت أقوى مما تتخيل!*\n📚 المذاكرة اليوم = نجاح الغد",
    "⭐ *لا تستسلم! المثابرة هي مفتاح التفوق!*\n🎯 ركز وانت هتوصل",
]

أذكار = [
    "🤲 *اللهم صل وسلم على سيدنا محمد*\n💝 اللهم صل على النبي",
    "🌸 *سبحان الله وبحمده*\n✨ سبحان الله العظيم",
    "💚 *استغفر الله العظيم وأتوب إليه*\n🌿 اللهم اغفر لي",
]

كلمات_محظورة = [
    "كس", "طيز", "زب", "شرموط", "عرص", "كلب", "حمار", "غبي", "أهبل"
]

قوانين_الجروب = (
    "📋 *قوانين الجروب*\n\n"
    "1. الاحترام المتبادل\n"
    "2. ممنوع السب والشتيمة\n"
    "3. ممنوع الاعلانات والسبام\n"
    "4. ممنوع نشر روابط بدون اذن\n\n"
    "مخالفة القوانين = تحذير، وبعد 3 تحذيرات حظر تلقائي."
)

# ==================== دوال Supabase ====================
async def سجل_مستخدم(user_id, الاسم, يوزرنيم):
    if not supabase:
        return
    try:
        supabase.table("مستخدمين").upsert({
            "user_id": user_id,
            "الاسم": الاسم,
            "يوزرنيم": يوزرنيم or "",
            "آخر_نشاط": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"سجل_مستخدم: {e}")

async def سجل_جروب(chat_id, اسم):
    if not supabase:
        return
    try:
        supabase.table("جروبات").upsert({
            "chat_id": chat_id,
            "اسم": اسم,
            "آخر_تحديث": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"سجل_جروب: {e}")

async def جيب_تحذيرات(chat_id, user_id):
    if not supabase:
        return 0
    try:
        r = supabase.table("تحذيرات").select("عدد").eq("chat_id", chat_id).eq("user_id", user_id).execute()
        return r.data[0]["عدد"] if r.data else 0
    except:
        return 0

async def حدث_تحذيرات(chat_id, user_id, عدد):
    if not supabase:
        return
    try:
        supabase.table("تحذيرات").upsert({
            "chat_id": chat_id,
            "user_id": user_id,
            "عدد": عدد
        }).execute()
    except:
        pass

async def سجل_حدث(نوع, تفاصيل):
    if not supabase:
        return
    try:
        supabase.table("سجل_أحداث").insert({
            "النوع": نوع,
            "التفاصيل": تفاصيل,
            "created_at": datetime.now().isoformat()
        }).execute()
    except:
        pass

async def جيب_أوامر_اللوحة():
    """جلب الأوامر من لوحة التحكم"""
    if not supabase:
        return []
    try:
        r = supabase.table("أوامر").select("*").eq("تم_التنفيذ", False).execute()
        return r.data or []
    except:
        return []

async def تحديث_حالة_الأمر(id_امر):
    if not supabase:
        return
    try:
        supabase.table("أوامر").update({"تم_التنفيذ": True}).eq("id", id_امر).execute()
    except:
        pass

# ==================== دوال البوت ====================
async def هو_ادمن(update, context):
    م = update.effective_user
    ش = update.effective_chat
    if ش.type == "private":
        return True
    ع = await context.bot.get_chat_member(ش.id, م.id)
    return ع.status in ["administrator", "creator"]

def فيه_كلمة_محظورة(نص):
    return any(ك in نص.lower() for ك in كلمات_محظورة)

def فيه_رابط(نص):
    return bool(re.search(r'http[s]?://|www\.|t\.me/', نص, re.IGNORECASE))

def قراءة_أسئلة(file_bytes):
    global أسئلة_البوت
    أسئلة_البوت = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1]:
                أسئلة_البوت.append({
                    "سؤال": str(row[0]),
                    "إجابة": str(row[1]),
                    "أ": str(row[2]) if row[2] else "",
                    "ب": str(row[3]) if row[3] else "",
                    "ج": str(row[4]) if row[4] else "",
                    "د": str(row[5]) if row[5] else "",
                    "شرح": str(row[6]) if len(row) > 6 and row[6] else "",
                })
        return len(أسئلة_البوت)
    except Exception as e:
        logging.error(f"قراءة أسئلة: {e}")
        return 0

def القائمة_الرئيسية():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔨 حظر", callback_data="حظر"), InlineKeyboardButton("🔓 فك الحظر", callback_data="فك_حظر")],
        [InlineKeyboardButton("🔇 كتم", callback_data="كتم"), InlineKeyboardButton("🔊 فك الكتم", callback_data="فك_كتم")],
        [InlineKeyboardButton("⚠️ تحذير", callback_data="تحذير"), InlineKeyboardButton("🗑 مسح", callback_data="مسح")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="إحصائيات"), InlineKeyboardButton("📋 القوانين", callback_data="قوانين")],
    ])

# ==================== معالجة أوامر اللوحة ====================
async def معالجة_أوامر_اللوحة(context: ContextTypes.DEFAULT_TYPE):
    """كل 5 ثواني يشوف لو في أوامر جديدة من لوحة التحكم"""
    try:
        ors = await جيب_أوامر_اللوحة()
        
        for امر in ors:
            نوع = امر["النوع"]
            بيانات = امر["البيانات"]
            
            if نوع == "broadcast":
                # إرسال إشعار لكل المستخدمين
                if supabase:
                    users = supabase.table("مستخدمين").select("user_id").execute()
                    for user in users.data or []:
                        try:
                            await context.bot.send_message(user["user_id"], بيانات.get("text", ""), parse_mode="Markdown")
                        except:
                            pass
                    await سجل_حدث("broadcast", f"إرسال إشعار لـ {len(users.data or [])} مستخدم")
            
            elif نوع == "direct_message":
                # إرسال رسالة لمستخدم معين
                try:
                    await context.bot.send_message(بيانات["user_id"], بيانات["text"], parse_mode="Markdown")
                    await سجل_حدث("direct_message", f"إرسال للمستخدم {بيانات['user_id']}")
                except Exception as e:
                    logging.error(f"direct_message: {e}")
            
            elif نوع == "ban_user":
                # حظر مستخدم
                try:
                    # حظر في كل الجروبات
                    groups = supabase.table("جروبات").select("chat_id").execute()
                    for g in groups.data or []:
                        try:
                            await context.bot.ban_chat_member(g["chat_id"], بيانات["user_id"])
                        except:
                            pass
                    await سجل_حدث("ban", f"حظر المستخدم {بيانات['user_id']}")
                except Exception as e:
                    logging.error(f"ban_user: {e}")
            
            elif نوع == "update_points":
                # تحديث نقاط المستخدم
                if supabase:
                    supabase.table("مستخدمين").update({
                        "نقاط": بيانات["points"],
                        "رتبة": بيانات.get("rank", "مبتدئ")
                    }).eq("user_id", بيانات["user_id"]).execute()
                    await سجل_حدث("update", f"تحديث نقاط المستخدم {بيانات['user_id']}")
            
            elif نوع == "group_message":
                # إرسال لجروب معين
                try:
                    await context.bot.send_message(بيانات["chat_id"], بيانات["text"], parse_mode="Markdown")
                    await سجل_حدث("group_message", f"إرسال للجروب {بيانات['chat_id']}")
                except:
                    pass
            
            elif نوع == "toggle_group":
                # تعطيل/تفعيل البوت في جروب
                if supabase:
                    supabase.table("جروبات").update({"نشط": بيانات["active"]}).eq("chat_id", بيانات["chat_id"]).execute()
            
            # تحديث حالة الأمر
            await تحديث_حالة_الأمر(امر["id"])
            
    except Exception as e:
        logging.error(f"معالجة_أوامر_اللوحة: {e}")

# ==================== إرسال سؤال ====================
async def إرسال_سؤال(context: ContextTypes.DEFAULT_TYPE):
    global index_سؤال, سؤال_حالي, إحصائيات_معسكر
    
    if not أسئلة_مخلوطة or index_سؤال >= len(أسئلة_مخلوطة):
        # المعسكر خلص
        for job in context.job_queue.get_jobs_by_name("أسئلة_معسكر"):
            job.schedule_removal()
        await context.bot.send_message(CHAT_ID, "🏆 *انتهى المعسكر!*\n\nبارك الله فيكم 🌟", parse_mode="Markdown")
        return
    
    سؤال_حالي = أسئلة_مخلوطة[index_سؤال]
    index_سؤال += 1
    إحصائيات_معسكر["أسئلة_بُعتت"] += 1
    
    خيارات = [سؤال_حالي['أ'], سؤال_حالي['ب'], سؤال_حالي['ج'], سؤال_حالي['د']]
    حروف = ['أ', 'ب', 'ج', 'د']
    رقم = حروف.index(سؤال_حالي['إجابة'])
    
    شرح = f"✅ الإجابة الصحيحة: {سؤال_حالي['إجابة']}) {سؤال_حالي[سؤال_حالي['إجابة']]}"
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
    
    # إشعار للأونر
    if OWNER_ID and م.id != OWNER_ID:
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n👤 {م.first_name}\n🆔 `{م.id}`", parse_mode="Markdown")
        except:
            pass
    
    await update.message.reply_text(
        "👋 *أهلاً! أنا بووووو*\n\n"
        "🔹 إدارة الأعضاء\n"
        "🔹 ذكاء اصطناعي بالمصري\n"
        "🔹 معسكرات أسئلة\n\n"
        "اختار من القائمة 👇",
        parse_mode="Markdown",
        reply_markup=القائمة_الرئيسية()
    )

async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ن = update.chat_member
    if ن.new_chat_member.user.id == (await context.bot.get_me()).id:
        await سجل_جروب(update.effective_chat.id, update.effective_chat.title or "جروب")
        if OWNER_ID:
            await context.bot.send_message(OWNER_ID, f"➕ *البوت اتضاف لجروب جديد!*\n📛 {update.effective_chat.title}\n🆔 `{update.effective_chat.id}`", parse_mode="Markdown")
        return
    
    if ن.new_chat_member.status == "member":
        ع = ن.new_chat_member.user
        await سجل_مستخدم(ع.id, ع.first_name, ع.username)
        await context.bot.send_message(update.effective_chat.id, f"👋 *أهلاً {ع.first_name}!*\n\n{قوانين_الجروب}", parse_mode="Markdown")

async def معالج_الأزرار(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    نصوص = {
        "مساعدة": "📖 *الدليل*\n\nرد على رسالة العضو واكتب:\nحظر | فك حظر | كتم | فك كتم | تحذير | مسح",
        "قوانين": قوانين_الجروب,
        "إحصائيات": "📊 *الإحصائيات*\n\n👥 مستخدمين مسجلين\n⚠️ محذّرين\n📚 أسئلة محملة",
    }
    
    await query.edit_message_text(
        نصوص.get(query.data, "❓ اختر من القائمة"),
        parse_mode="Markdown",
        reply_markup=القائمة_الرئيسية()
    )

async def معالج_الملفات(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    if م.id != OWNER_ID:
        await update.message.reply_text("❌ للأدمن فقط.")
        return
    
    document = update.message.document
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ ارفع ملف Excel فقط.")
        return
    
    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    
    عدد = قراءة_أسئلة(bytes(file_bytes))
    if عدد > 0:
        context.user_data['انتظر_مادة'] = True
        context.user_data['عدد_أسئلة'] = عدد
        await update.message.reply_text(f"✅ تم رفع *{عدد}* سؤال!\n\n📚 ما اسم المادة؟", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ مفيش أسئلة في الملف.")

async def معالج_الرسائل(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    نص = update.message.text.strip()
    رد_على = update.message.reply_to_message
    في_الخاص = update.effective_chat.type == "private"
    م = update.effective_user
    
    # ====== أوامر الأونر في الخاص ======
    if في_الخاص and م.id == OWNER_ID:
        
        # انتظار اسم المادة
        if context.user_data.get('انتظر_مادة'):
            context.user_data['اسم_المادة'] = نص
            context.user_data['انتظر_مادة'] = False
            context.user_data['انتظر_وقت'] = True
            await update.message.reply_text(f"✅ المادة: *{نص}*\n\n⏱️ كل كام دقيقة تبعت سؤال؟", parse_mode="Markdown")
            return
        
        # انتظار الوقت
        if context.user_data.get('انتظر_وقت') and نص.isdigit():
            global index_سؤال, أسئلة_مخلوطة, معسكر_نشط, إحصائيات_معسكر
            دقائق = int(nص)
            
            # إنهاء المعسكر القديم لو موجود
            for job in context.job_queue.get_jobs_by_name("أسئلة_معسكر"):
                job.schedule_removal()
            
            # خلط الأسئلة
            أسئلة_مخلوطة = أسئلة_البوت.copy()
            random.shuffle(أسئلة_مخلوطة)
            index_سؤال = 0
            إحصائيات_معسكر = {"أسئلة_بُعتت": 0, "إجابات_صحيحة": 0}
            معسكر_نشط = True
            
            # بدء المعسكر
            context.user_data['انتظر_وقت'] = False
            context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=10, name="أسئلة_معسكر")
            
            await update.message.reply_text(
                f"🏕️ *المعسكر جاهز!*\n\n"
                f"📚 {context.user_data.get('اسم_المادة', 'مادة')}\n"
                f"⏱️ سؤال كل {دقائق} دقيقة\n"
                f"📝 {len(أسئلة_مخلوطة)} سؤال\n\n"
                f"🚀 يبدأ خلال ثواني...",
                parse_mode="Markdown"
            )
            return
        
        # بعت للكل
        if نص.startswith("بعت للكل:"):
            رسالة = نص.replace("بعت للكل:", "").strip()
            if not رسالة:
                await update.message.reply_text("❌ اكتب الرسالة بعد :")
                return
            
            if not supabase:
                await update.message.reply_text("❌ Supabase مش شغال")
                return
            
            await update.message.reply_text("⏳ جاري الإرسال...")
            users = supabase.table("مستخدمين").select("user_id").execute()
            نجح = 0
            for user in users.data or []:
                try:
                    await context.bot.send_message(user["user_id"], رسالة, parse_mode="Markdown")
                    نجح += 1
                except:
                    pass
            
            await update.message.reply_text(f"✅ تم الإرسال لـ {نجح} مستخدم")
            await سجل_حدث("broadcast", f"إرسال لـ {نجح} مستخدم")
            return
        
        # جروباتي
        if نص in ["جروباتي", "جروبات البوت"]:
            if not supabase:
                await update.message.reply_text("❌ Supabase مش شغال")
                return
            
            groups = supabase.table("جروبات").select("*").execute()
            if not groups.data:
                await update.message.reply_text("❌ البوت مش في أي جروب")
                return
            
            result = "📋 *الجروبات:*\n\n"
            for i, g in enumerate(groups.data, 1):
                result += f"{i}. {g.get('اسم', 'بدون اسم')} — `{g['chat_id']}`\n"
            await update.message.reply_text(result, parse_mode="Markdown")
            return
        
        # إحصائيات المعسكر
        if نص in ["إحصائيات المعسكر", "كام سؤال"]:
            متبقي = len(أسئلة_مخلوطة) - index_سؤال
            await update.message.reply_text(
                f"📊 *إحصائيات المعسكر*\n\n"
                f"✅ أسئلة اتبعتت: {إحصائيات_معسكر['أسئلة_بُعتت']}\n"
                f"📚 إجمالي: {len(أسئلة_مخلوطة)}\n"
                f"⏳ متبقي: {متبقي}",
                parse_mode="Markdown"
            )
            return
        
        # وقف المعسكر
        if نص in ["وقف", "وقف المعسكر", "إنهاء"]:
            for job in context.job_queue.get_jobs_by_name("أسئلة_معسكر"):
                job.schedule_removal()
            معسكر_نشط = False
            await update.message.reply_text("✅ تم إيقاف المعسكر")
            return
        
        # قفل الجروب
        if نص in ["اقفل الجروب", "قفل الجروب"] and CHAT_ID:
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=False))
                await update.message.reply_text("🔒 تم قفل الجروب")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
        
        # فتح الجروب
        if نص in ["افتح الجروب", "فتح الجروب"] and CHAT_ID:
            try:
                await context.bot.set_chat_permissions(CHAT_ID, ChatPermissions(can_send_messages=True))
                await update.message.reply_text("🔓 تم فتح الجروب")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
    
    # ====== فلتر تلقائي ======
    if not في_الخاص and not await هو_ادمن(update, context):
        if فيه_كلمة_محظورة(نص):
            try:
                await update.message.delete()
                ع = await جيب_تحذيرات(update.effective_chat.id, م.id)
                ج = ع + 1
                await حدث_تحذيرات(update.effective_chat.id, م.id, ج)
                if ج >= 3:
                    await context.bot.ban_chat_member(update.effective_chat.id, م.id)
                    await update.message.reply_text(f"🚫 تم حظر {م.first_name} تلقائياً!")
                else:
                    await update.message.reply_text(f"⚠️ {م.first_name} تحذير {ج}/3")
            except:
                pass
            return
        
        if فيه_رابط(نص):
            try:
                await update.message.delete()
                await update.message.reply_text(f"🔗 {م.first_name} ممنوع نشر الروابط!")
            except:
                pass
            return
    
    # ====== أوامر الإدارة ======
    if رد_على and await هو_ادمن(update, context):
        ع = رد_على.from_user
        
        if نص == "حظر":
            try:
                await context.bot.ban_chat_member(update.effective_chat.id, ع.id)
                await update.message.reply_text(f"🔨 تم حظر {ع.first_name}")
            except Exception as e:
                await update.message.reply_text(f"❌ {e}")
            return
        
        if نص == "فك حظر":
            try:
                await context.bot.unban_chat_member(update.effective_chat.id, ع.id)
                await update.message.reply_text(f"🔓 تم فك الحظر عن {ع.first_name}")
            except:
                pass
            return
        
        if نص == "كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, ع.id, permissions=ChatPermissions(can_send_messages=False))
                await update.message.reply_text(f"🔇 تم كتم {ع.first_name}")
            except:
                pass
            return
        
        if نص == "فك كتم":
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, ع.id, permissions=ChatPermissions(can_send_messages=True))
                await update.message.reply_text(f"🔊 تم فك الكتم عن {ع.first_name}")
            except:
                pass
            return
        
        if نص == "مسح":
            try:
                await رد_على.delete()
                await update.message.delete()
            except:
                pass
            return
        
        if نص == "تحذير":
            ت = await جيب_تحذيرات(update.effective_chat.id, ع.id)
            ج = ت + 1
            await حدث_تحذيرات(update.effective_chat.id, ع.id, ج)
            if ج >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, ع.id)
                    await update.message.reply_text(f"🚫 تم حظر {ع.first_name} بعد 3 تحذيرات!")
                except:
                    pass
            else:
                await update.message.reply_text(f"⚠️ تحذير {ج}/3 لـ {ع.first_name}")
            return
    
    # ====== قوانين ======
    if نص in ["القوانين", "قوانين"]:
        await update.message.reply_text(قوانين_الجروب, parse_mode="Markdown")
        return
    
    # ====== chat_id ======
    if نص == "chat_id" and await هو_ادمن(update, context):
        await update.message.reply_text(f"🆔 Chat ID: `{update.effective_chat.id}`", parse_mode="Markdown")
        return
    
    # ====== ذكاء اصطناعي ======
    بوت_info = await context.bot.get_me()
    اسم_البوت = f"@{بوت_info.username}"
    
    اتذكر = اسم_البوت.lower() in نص.lower()
    فيه_سؤال = "؟" in نص or "?" in نص
    
    if في_الخاص or اتذكر or فيه_سؤال:
        س = نص.replace(اسم_البوت, "").strip()
        if not س:
            return
        
        try:
            await context.bot.send_chat_action(update.effective_chat.id, "typing")
            رد = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": f"أنت مساعد ذكي اسمك بووووو، صنعك {اسم_الصانع}. لازم تتكلم بالعامية المصرية دايماً. لو حد سألك مين صنعك قوله {اسم_الصانع}."},
                    {"role": "user", "content": س}
                ]
            )
            await update.message.reply_text(رد.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")

# ==================== تشغيل البوت ====================
async function post_init(app: Application):
    """بعد تشغيل البوت"""
    print("✅ البوت شغال...")
    # بدء جلب أوامر اللوحة كل 5 ثواني
    app.job_queue.run_repeating(معالجة_أوامر_اللوحة, interval=5, first=1)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(ترحيب_عضو_جديد, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(معالج_الأزرار))
    app.add_handler(MessageHandler(filters.Document.ALL, معالج_الملفات))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, معالج_الرسائل))
    
    # Post init
    app.post_init = post_init
    
    print("✅ التشغيل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
