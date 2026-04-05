import io
import random
import logging
import openpyxl
from telegram.ext import ContextTypes
from config import رسائل_تحفيزية, أذكار

# بيانات المعسكرات لكل جروب في الذاكرة
معسكرات = {}
نقاط_المستخدمين = {}


def جيب_بيانات_جروب(chat_id):
    if chat_id not in معسكرات:
        معسكرات[chat_id] = {
            "أسئلة": [], "مخلوطة": [], "index": 0,
            "إحصائيات": {"أسئلة_بُعتت": 0},
            "info": {"اسم_المادة": "", "كل_دقايق": 1},
        }
    return معسكرات[chat_id]

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

def أضف_نقاط(chat_id, user_id, نقاط):
    if chat_id not in نقاط_المستخدمين:
        نقاط_المستخدمين[chat_id] = {}
    if user_id not in نقاط_المستخدمين[chat_id]:
        نقاط_المستخدمين[chat_id][user_id] = 0
    نقاط_المستخدمين[chat_id][user_id] += نقاط

def جيب_ترتيب(chat_id):
    if chat_id not in نقاط_المستخدمين:
        return []
    مرتب = sorted(نقاط_المستخدمين[chat_id].items(), key=lambda x: x[1], reverse=True)
    return مرتب[:10]

def ابدأ_معسكر(context, chat_id, اسم_المادة, دقائق, عدد_أسئلة):
    for job in (
        context.job_queue.get_jobs_by_name(f"أسئلة_{chat_id}") +
        context.job_queue.get_jobs_by_name(f"تحفيز_{chat_id}") +
        context.job_queue.get_jobs_by_name(f"أذكار_{chat_id}")
    ):
        job.schedule_removal()
    بيانات = جيب_بيانات_جروب(chat_id)
    بيانات["مخلوطة"] = بيانات["أسئلة"].copy()
    random.shuffle(بيانات["مخلوطة"])
    بيانات["index"] = 0
    بيانات["إحصائيات"] = {"أسئلة_بُعتت": 0}
    if chat_id in نقاط_المستخدمين:
        نقاط_المستخدمين[chat_id] = {}
    context.job_queue.run_once(بدء_المعسكر, 5, data={"chat_id": chat_id, "اسم_المادة": اسم_المادة, "عدد_أسئلة": عدد_أسئلة, "كل_دقايق": دقائق}, name=f"بدء_{chat_id}")
    context.job_queue.run_repeating(إرسال_سؤال, interval=دقائق * 60, first=15, data={"chat_id": chat_id}, name=f"أسئلة_{chat_id}")
    context.job_queue.run_repeating(إرسال_تحفيز, interval=دقائق * 60 * 2, first=دقائق * 60, data={"chat_id": chat_id}, name=f"تحفيز_{chat_id}")
    context.job_queue.run_repeating(إرسال_ذكر, interval=15 * 60, first=15 * 60, data={"chat_id": chat_id}, name=f"أذكار_{chat_id}")


async def بدء_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    await context.bot.send_message(
        data["chat_id"],
        f"🏕️ *معسكر أسئلة جديد!*\n\n"
        f"📚 *المادة:* {data['اسم_المادة']}\n"
        f"📝 *عدد الأسئلة:* {data['عدد_أسئلة']} سؤال\n"
        f"⏱️ *سؤال كل:* {data['كل_دقايق']} دقيقة\n\n"
        "🤲 اللهم علمنا ما ينفعنا وانفعنا بما علمتنا\n\nيلا نذاكر! 💪🔥",
        parse_mode="Markdown"
    )

async def نهاية_المعسكر(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    ترتيب = جيب_ترتيب(chat_id)
    رسالة_ترتيب = ""
    if ترتيب:
        ميداليات = ["🥇", "🥈", "🥉"]
        رسالة_ترتيب = "\n\n🏆 *أفضل المشاركين:*\n"
        for i, (uid, نقاط) in enumerate(ترتيب[:3]):
            م = ميداليات[i] if i < 3 else f"{i+1}."
            رسالة_ترتيب += f"{م} `{uid}` — {نقاط} نقطة\n"
    await context.bot.send_message(
        chat_id,
        f"🏆 *انتهى المعسكر!*\n\nبارك الله فيكم 🌟\n\n"
        f"🤲 اللهم اجعل ما تعلمناه نافعاً\n\nالحمد لله الذي بنعمته تتم الصالحات 🌹"
        f"{رسالة_ترتيب}",
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
