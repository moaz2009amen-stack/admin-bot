import re
import logging
from datetime import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, BotCommand
from telegram.ext import ContextTypes

from config import (
    OWNER_ID, OWNER_USERNAME, VODAFONE_NUMBER, سعر_الاشتراك,
    قوانين_الجروب, دليل_المستخدم, برومت_الأسئلة, كلمات_محظورة
)
from database import (
    سجل_مستخدم, سجل_جروب, جيب_جروبات_المستخدم, جيب_كل_الجروبات,
    جيب_owner_id, ai_مفعل_للجروب, فعّل_ai, وقف_ai,
    جيب_تحذيرات, حدث_تحذيرات, جيب_إحصائيات,
    جيب_طلبات_الاشتراك, جيب_مشتركين_ai, سجل_طلب_اشتراك, supabase
)
from camp import (
    جيب_بيانات_جروب, قراءة_أسئلة, ابدأ_معسكر,
    إرسال_سؤال, نهاية_المعسكر, جيب_ترتيب
)
from ai import اسأل_ai


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

async def تسجيل_جروب_تلقائي(chat_id, title, context):
    try:
        أعضاء = await context.bot.get_chat_administrators(chat_id)
        owner = next((a.user.id for a in أعضاء if a.status == "creator"), None)
        await سجل_جروب(chat_id, title or "جروب", owner)
    except Exception as e:
        logging.error(f"تسجيل_جروب_تلقائي: {e}")


# ==================== قوائم ====================
def قائمة_سوبر_أدمن():
    سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}" if سعر_الاشتراك['قيمة'] else "غير محدد"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات", callback_data="super_إحصائيات"), InlineKeyboardButton("🏘 كل الجروبات", callback_data="super_جروبات")],
        [InlineKeyboardButton("🔔 طلبات AI", callback_data="super_طلبات"), InlineKeyboardButton("🤖 مشتركين AI", callback_data="super_مشتركين")],
        [InlineKeyboardButton("📢 إعلان للكل", callback_data="super_إعلان"), InlineKeyboardButton(f"💰 السعر: {سعر_نص}", callback_data="super_سعر")],
        [InlineKeyboardButton("📋 تقرير الآن", callback_data="super_تقرير")],
    ])

def قائمة_جروبات_سوبر(جروبات):
    أزرار = [[InlineKeyboardButton(f"🏘 {ج.get('اسم', 'جروب')}", callback_data=f"sadmin_جروب_{ج['chat_id']}")] for ج in جروبات]
    أزرار.append([InlineKeyboardButton("🔙 رجوع", callback_data="super_رئيسية")])
    return InlineKeyboardMarkup(أزرار)

def قائمة_تحكم_جروب_سوبر(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تفعيل AI", callback_data=f"sadmin_aion_{chat_id}"), InlineKeyboardButton("🔴 وقف AI", callback_data=f"sadmin_aioff_{chat_id}")],
        [InlineKeyboardButton("🚪 إخراج البوت", callback_data=f"sadmin_طرد_{chat_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="super_جروبات")],
    ])

def قائمة_مشتركين_ai_لوحة(مشتركين):
    أزرار = [[InlineKeyboardButton(f"❌ وقف — جروب {م['chat_id']}", callback_data=f"sadmin_aioff_{م['chat_id']}")] for م in مشتركين]
    أزرار.append([InlineKeyboardButton("🔙 رجوع", callback_data="super_رئيسية")])
    return InlineKeyboardMarkup(أزرار)

def قائمة_جروبات_المستخدم(جروبات):
    أزرار = [[InlineKeyboardButton(f"🏘 {ج.get('اسم', 'جروب')}", callback_data=f"myjrp_{ج['chat_id']}")] for ج in جروبات]
    أزرار.append([InlineKeyboardButton("🔄 تحديث", callback_data="my_جروبات"), InlineKeyboardButton("📖 الدليل", callback_data="دليل")])
    return InlineKeyboardMarkup(أزرار)

def قائمة_تحكم_جروب(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 رفع أسئلة", callback_data=f"grp_رفع_{chat_id}"), InlineKeyboardButton("❓ سؤال الآن", callback_data=f"grp_سؤال_{chat_id}")],
        [InlineKeyboardButton("⏹ وقف المعسكر", callback_data=f"grp_وقف_{chat_id}"), InlineKeyboardButton("📊 إحصائيات", callback_data=f"grp_إحصائيات_{chat_id}")],
        [InlineKeyboardButton("🏆 الترتيب", callback_data=f"grp_ترتيب_{chat_id}"), InlineKeyboardButton("📋 القوانين", callback_data=f"grp_قوانين_{chat_id}")],
        [InlineKeyboardButton("🔒 قفل", callback_data=f"grp_قفل_{chat_id}"), InlineKeyboardButton("🔓 فتح", callback_data=f"grp_فتح_{chat_id}")],
        [InlineKeyboardButton("🤖 اشتراك AI 💎", callback_data=f"grp_ai_{chat_id}")],
        [InlineKeyboardButton("🔙 جروباتي", callback_data="my_جروبات")],
    ])

def القائمة_الرئيسية_مستخدم():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏘 جروباتي", callback_data="my_جروبات")],
        [InlineKeyboardButton("📖 دليل الاستخدام", callback_data="دليل")],
        [InlineKeyboardButton("📝 برومت الأسئلة", callback_data="برومت")],
        [InlineKeyboardButton("💎 اشتراك AI", callback_data="اشتراك_ai")],
    ])

def قائمة_اختيار_جروب_للأسئلة(جروبات):
    أزرار = [[InlineKeyboardButton(f"📚 {ج.get('اسم', 'جروب')}", callback_data=f"upload_to_{ج['chat_id']}")] for ج in جروبات]
    أزرار.append([InlineKeyboardButton("❌ إلغاء", callback_data="my_جروبات")])
    return InlineKeyboardMarkup(أزرار)


# ==================== Command Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    await سجل_مستخدم(م.id, م.first_name, م.username)

    if م.id == OWNER_ID:
        إحصاء = await جيب_إحصائيات()
        سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}" if سعر_الاشتراك['قيمة'] else "غير محدد"
        await update.message.reply_text(
            f"👑 *أهلاً يا Moaz!*\n\n"
            f"👥 المستخدمين: {إحصاء.get('مستخدمين', 0)}\n"
            f"🏘 الجروبات: {إحصاء.get('جروبات', 0)}\n"
            f"🤖 مشتركين AI: {إحصاء.get('مشتركين_ai', 0)}\n"
            f"💰 سعر الاشتراك: {سعر_نص}",
            parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
        )
        return

    if OWNER_ID != 0:
        ي = f"@{م.username}" if م.username else "مفيش يوزرنيم"
        try:
            await context.bot.send_message(OWNER_ID, f"🆕 *مستخدم جديد!*\n\n👤 {م.first_name}\n🔗 {ي}\n🆔 `{م.id}`", parse_mode="Markdown")
        except: pass

    جروبات = await جيب_جروبات_المستخدم(م.id)
    سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}" if سعر_الاشتراك['قيمة'] else ""
    رسالة = (
        f"👋 *أهلاً {م.first_name}! أنا بووووو* 🤖\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🆓 *مجاناً:* إدارة أعضاء + فلتر + أسئلة\n"
        f"💎 *بريميوم:* ذكاء اصطناعي{f' ({سعر_نص}/شهر)' if سعر_نص else ''}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "اختار من القائمة 👇"
    )
    if جروبات:
        await update.message.reply_text(رسالة, parse_mode="Markdown", reply_markup=قائمة_جروبات_المستخدم(جروبات))
    else:
        await update.message.reply_text(
            رسالة + "\n\n⚠️ *ضيف البوت في جروبك وابعت أي رسالة هناك*",
            parse_mode="Markdown", reply_markup=القائمة_الرئيسية_مستخدم()
        )

async def ctrl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    م = update.effective_user
    ش = update.effective_chat
    if م.id == OWNER_ID and ش.type == "private":
        إحصاء = await جيب_إحصائيات()
        await update.message.reply_text(
            f"👑 *لوحة السوبر أدمن*\n\n👥 {إحصاء.get('مستخدمين', 0)} مستخدم\n🏘 {إحصاء.get('جروبات', 0)} جروب\n🤖 {إحصاء.get('مشتركين_ai', 0)} مشترك AI",
            parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
        )
        return
    if ش.type != "private":
        if not await هو_ادمن(update, context):
            await update.message.reply_text("❌ للأدمن فقط.")
            return
        await تسجيل_جروب_تلقائي(ش.id, ش.title, context)
        await update.message.reply_text(
            f"🎛 *لوحة تحكم {ش.title}*",
            parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(ش.id)
        )
        return
    await update.message.reply_text("استخدم /start 👇")

async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(برومت_الأسئلة, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(دليل_المستخدم, parse_mode="Markdown", reply_markup=القائمة_الرئيسية_مستخدم())

async def setup_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "القائمة الرئيسية"),
        BotCommand("ctrl", "لوحة التحكم"),
        BotCommand("prompt", "برومت عمل ملف الأسئلة"),
        BotCommand("help", "دليل الاستخدام"),
    ])

async def ترحيب_عضو_جديد(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ن = update.chat_member
    ع = ن.new_chat_member.user
    ش = update.effective_chat
    بوت = await context.bot.get_me()
    if ع.id == بوت.id:
        await تسجيل_جروب_تلقائي(ش.id, ش.title, context)
        if OWNER_ID != 0:
            try:
                await context.bot.send_message(OWNER_ID, f"➕ *جروب جديد!*\n\n📛 {ش.title}\n🆔 `{ش.id}`", parse_mode="Markdown")
            except: pass
        await context.bot.send_message(ش.id, "👋 *أهلاً! أنا بووووو*\n\n🔹 إدارة الأعضاء\n🔹 فلتر تلقائي\n🔹 معسكرات أسئلة\n\nالأدمن يكتب /ctrl 🎛", parse_mode="Markdown")
        return
    if ن.new_chat_member.status == "member":
        await سجل_مستخدم(ع.id, ع.first_name, ع.username)
        if OWNER_ID != 0:
            try:
                ي = f"@{ع.username}" if ع.username else "مفيش يوزرنيم"
                await context.bot.send_message(OWNER_ID, f"👤 *عضو جديد في {ش.title}*\n{ع.first_name} — {ي}\n🆔 `{ع.id}`", parse_mode="Markdown")
            except: pass
        await context.bot.send_message(ش.id, f"👋 *أهلاً {ع.first_name}!*\n\nيسعدنا انضمامك 🎉\n\n{قوانين_الجروب}", parse_mode="Markdown")

async def تقرير_يومي(context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID == 0: return
    إحصاء = await جيب_إحصائيات()
    await context.bot.send_message(
        OWNER_ID,
        f"📋 *التقرير اليومي*\n\n"
        f"👥 المستخدمين: {إحصاء.get('مستخدمين', 0)}\n"
        f"🏘 الجروبات: {إحصاء.get('جروبات', 0)}\n"
        f"🤖 مشتركين AI: {إحصاء.get('مشتركين_ai', 0)}\n"
        f"⚠️ المحذّرين: {إحصاء.get('محذورين', 0)}",
        parse_mode="Markdown"
    )


# ==================== Callback Handler ====================
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
            سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}" if سعر_الاشتراك['قيمة'] else "غير محدد"
            await query.edit_message_text(
                f"📊 *إحصائيات كاملة*\n\n👥 {إحصاء.get('مستخدمين',0)}\n🏘 {إحصاء.get('جروبات',0)}\n⚠️ {إحصاء.get('محذورين',0)}\n🤖 {إحصاء.get('مشتركين_ai',0)}\n💰 {سعر_نص}",
                parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
            )
        elif أمر == "جروبات":
            جروبات = await جيب_كل_الجروبات()
            if not جروبات:
                await query.answer("❌ مفيش جروبات", show_alert=True); return
            await query.edit_message_text("🏘 *كل الجروبات:*", parse_mode="Markdown", reply_markup=قائمة_جروبات_سوبر(جروبات))
        elif أمر == "مشتركين":
            مشتركين = await جيب_مشتركين_ai()
            if not مشتركين:
                await query.answer("❌ مفيش مشتركين", show_alert=True); return
            نص = "🤖 *مشتركين AI:*\n\n" + "\n".join(f"👤 `{م_اش['user_id']}` — جروب `{م_اش['chat_id']}`" for م_اش in مشتركين)
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=قائمة_مشتركين_ai_لوحة(مشتركين))
        elif أمر == "طلبات":
            طلبات = await جيب_طلبات_الاشتراك()
            if not طلبات:
                await query.answer("✅ مفيش طلبات", show_alert=True); return
            نص = "🔔 *طلبات تفعيل AI:*\n\n"
            أزرار = []
            for ط in طلبات:
                نص += f"👤 `{ط['user_id']}` — جروب `{ط['chat_id']}`\n"
                أزرار.append([
                    InlineKeyboardButton("✅ فعّل", callback_data=f"activate_{ط['user_id']}_{ط['chat_id']}"),
                    InlineKeyboardButton("❌ ارفض", callback_data=f"reject_{ط['user_id']}_{ط['chat_id']}"),
                ])
            أزرار.append([InlineKeyboardButton("🔙 رجوع", callback_data="super_رئيسية")])
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(أزرار))
        elif أمر == "إعلان":
            context.user_data["انتظر_إعلان"] = True
            await query.edit_message_text("📢 *اكتب نص الإعلان:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="super_رئيسية")]]))
        elif أمر == "سعر":
            context.user_data["انتظر_سعر"] = True
            await query.edit_message_text("💰 *اكتب سعر الاشتراك:*\n\nمثال: `50 جنيه`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="super_رئيسية")]]))
        elif أمر == "تقرير":
            إحصاء = await جيب_إحصائيات()
            await query.edit_message_text(
                f"📋 *التقرير*\n\n👥 {إحصاء.get('مستخدمين',0)}\n🏘 {إحصاء.get('جروبات',0)}\n🤖 {إحصاء.get('مشتركين_ai',0)}\n⚠️ {إحصاء.get('محذورين',0)}",
                parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
            )
        elif أمر == "رئيسية":
            إحصاء = await جيب_إحصائيات()
            سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}" if سعر_الاشتراك['قيمة'] else "غير محدد"
            await query.edit_message_text(
                f"👑 *لوحة السوبر أدمن*\n\n👥 {إحصاء.get('مستخدمين',0)} مستخدم\n🏘 {إحصاء.get('جروبات',0)} جروب\n🤖 {إحصاء.get('مشتركين_ai',0)} مشترك\n💰 {سعر_نص}",
                parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن()
            )
        return

    # ===== تحكم سوبر أدمن في جروب =====
    if بيانات.startswith("sadmin_") and م.id == OWNER_ID:
        parts = بيانات.replace("sadmin_", "").split("_")
        أمر = parts[0]
        chat_id = int(parts[1]) if len(parts) > 1 else None
        if not chat_id: return
        if أمر == "جروب":
            مفعل = await ai_مفعل_للجروب(chat_id)
            await query.edit_message_text(
                f"🏘 جروب `{chat_id}`\n🤖 AI: {'✅ مفعّل' if مفعل else '❌ موقف'}",
                parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب_سوبر(chat_id)
            )
        elif أمر == "طرد":
            try:
                await context.bot.leave_chat(chat_id)
                if supabase: supabase.table("جروبات").delete().eq("chat_id", chat_id).execute()
                await query.answer("✅ تم إخراج البوت", show_alert=True)
                جروبات = await جيب_كل_الجروبات()
                await query.edit_message_text("🏘 *كل الجروبات:*", parse_mode="Markdown", reply_markup=قائمة_جروبات_سوبر(جروبات))
            except Exception as e:
                await query.answer(f"❌ {e}", show_alert=True)
        elif أمر == "aioff":
            await وقف_ai(chat_id)
            await query.answer("✅ تم وقف AI", show_alert=True)
        elif أمر == "aion":
            owner = await جيب_owner_id(chat_id)
            if owner and await فعّل_ai(owner, chat_id):
                try: await context.bot.send_message(owner, "🎉 *تم تفعيل AI في جروبك!*", parse_mode="Markdown")
                except: pass
                await query.answer("✅ تم تفعيل AI", show_alert=True)
        return

    # ===== تفعيل / رفض =====
    if بيانات.startswith("activate_") and م.id == OWNER_ID:
        parts = بيانات.split("_")
        user_id, chat_id = int(parts[1]), int(parts[2])
        if await فعّل_ai(user_id, chat_id):
            try: await context.bot.send_message(user_id, "🎉 *تم تفعيل AI في جروبك!*\n\nاذكر اسم البوت أو اكتب ؟ 🤖", parse_mode="Markdown")
            except: pass
            await query.answer("✅ تم التفعيل!", show_alert=True)
        else:
            await query.answer("❌ فشل التفعيل!", show_alert=True)
        return

    if بيانات.startswith("reject_") and م.id == OWNER_ID:
        user_id = int(بيانات.split("_")[1])
        try: await context.bot.send_message(user_id, f"❌ *تم رفض طلب الاشتراك*\n\nللاستفسار تواصل مع {OWNER_USERNAME}", parse_mode="Markdown")
        except: pass
        await query.answer("تم الرفض", show_alert=True)
        return

    # ===== اختيار جروب لرفع الأسئلة =====
    if بيانات.startswith("upload_to_"):
        chat_id = int(بيانات.replace("upload_to_", ""))
        owner = await جيب_owner_id(chat_id)
        if م.id != owner and م.id != OWNER_ID:
            await query.answer("❌ مش أونر!", show_alert=True); return
        context.user_data['chat_id_أسئلة'] = chat_id
        context.user_data['انتظر_ملف_من_خاص'] = True
        try:
            chat_info = await context.bot.get_chat(chat_id)
            اسم = chat_info.title or str(chat_id)
        except:
            اسم = str(chat_id)
        await query.edit_message_text(
            f"📚 *ابعت ملف Excel للجروب:*\n_{اسم}_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="my_جروبات")]])
        )
        return

    # ===== جروبات المستخدم =====
    if بيانات == "my_جروبات":
        جروبات = await جيب_جروبات_المستخدم(م.id)
        if not جروبات:
            await query.edit_message_text("❌ مش لاقي جروبات\n\nضيف البوت في جروبك وابعت أي رسالة هناك", parse_mode="Markdown", reply_markup=القائمة_الرئيسية_مستخدم())
            return
        await query.edit_message_text("🏘 *جروباتك:*", parse_mode="Markdown", reply_markup=قائمة_جروبات_المستخدم(جروبات))
        return

    if بيانات.startswith("myjrp_"):
        chat_id = int(بيانات.replace("myjrp_", ""))
        owner = await جيب_owner_id(chat_id)
        if owner != م.id and م.id != OWNER_ID:
            await query.answer("❌ مش أونر!", show_alert=True); return
        try:
            chat_info = await context.bot.get_chat(chat_id)
            اسم = chat_info.title or "الجروب"
        except:
            اسم = "الجروب"
        await query.edit_message_text(f"🎛 *لوحة تحكم {اسم}*", parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(chat_id))
        return

    if بيانات == "دليل":
        جروبات = await جيب_جروبات_المستخدم(م.id)
        await query.edit_message_text(دليل_المستخدم, parse_mode="Markdown", reply_markup=قائمة_جروبات_المستخدم(جروبات) if جروبات else القائمة_الرئيسية_مستخدم())
        return

    if بيانات == "برومت":
        await query.edit_message_text(برومت_الأسئلة, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="my_جروبات")]]))
        return

    if بيانات == "اشتراك_ai":
        سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}/شهر" if سعر_الاشتراك['قيمة'] else "تواصل مع الأدمن"
        try:
            ي = f"@{م.username}" if م.username else "مفيش يوزرنيم"
            await context.bot.send_message(OWNER_ID, f"💰 *طلب اشتراك AI!*\n\n👤 {م.first_name}\n🔗 {ي}\n🆔 `{م.id}`", parse_mode="Markdown")
        except: pass
        await query.edit_message_text(
            f"💎 *اشتراك الذكاء الاصطناعي*\n\n💰 السعر: {سعر_نص}\n\n📱 *فودافون كاش:*\n`{VODAFONE_NUMBER}`\n\nبعد الدفع تواصل مع {OWNER_USERNAME}\n\n✅ سيتم التفعيل خلال ساعة",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="my_جروبات")]])
        )
        return

    # ===== تحكم الجروب =====
    if بيانات.startswith("grp_"):
        parts = بيانات.replace("grp_", "").split("_")
        أمر = parts[0]
        chat_id = int(parts[1]) if len(parts) > 1 else None
        if not chat_id: return
        owner = await جيب_owner_id(chat_id)
        if م.id != owner and م.id != OWNER_ID:
            try:
                عضو = await context.bot.get_chat_member(chat_id, م.id)
                if عضو.status not in ["administrator", "creator"]:
                    await query.answer("❌ مش أدمن!", show_alert=True); return
            except:
                await query.answer("❌ مش قادر أتحقق", show_alert=True); return

        بيانات_جروب = جيب_بيانات_جروب(chat_id)

        if أمر == "رفع":
            context.user_data['chat_id_أسئلة'] = chat_id
            context.user_data['انتظر_ملف_من_خاص'] = True
            await query.edit_message_text("📚 *ابعت ملف Excel للأسئلة*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data=f"myjrp_{chat_id}")]]))
        elif أمر == "إحصائيات":
            await query.edit_message_text(
                f"📊 *إحصائيات*\n\n✅ {بيانات_جروب['إحصائيات']['أسئلة_بُعتت']} سؤال\n📚 {len(بيانات_جروب['مخلوطة'])} إجمالي\n⏳ {len(بيانات_جروب['مخلوطة']) - بيانات_جروب['index']} متبقي",
                parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(chat_id)
            )
        elif أمر == "ترتيب":
            ترتيب = جيب_ترتيب(chat_id)
            if not ترتيب:
                await query.answer("❌ مفيش نقاط لسه", show_alert=True); return
            ميداليات = ["🥇", "🥈", "🥉"]
            نص = "🏆 *لوحة الترتيب:*\n\n"
            for i, (uid, نقاط) in enumerate(ترتيب):
                نص += f"{ميداليات[i] if i < 3 else f'{i+1}.'} `{uid}` — {نقاط} نقطة\n"
            await query.edit_message_text(نص, parse_mode="Markdown", reply_markup=قائمة_تحكم_جروب(chat_id))
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
            await query.answer("✅ تم", show_alert=True)
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
                await query.edit_message_text("✅ *AI مفعّل في جروبك!* 🤖", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔴 وقف AI", callback_data=f"sadmin_aioff_{chat_id}")], [InlineKeyboardButton("🔙 رجوع", callback_data=f"myjrp_{chat_id}")]]))
            else:
                سعر_نص = f"{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}/شهر" if سعر_الاشتراك['قيمة'] else "تواصل مع الأدمن"
                await سجل_طلب_اشتراك(م.id, chat_id, م.first_name)
                try:
                    ي = f"@{م.username}" if م.username else "مفيش يوزرنيم"
                    await context.bot.send_message(OWNER_ID, f"💰 *طلب اشتراك AI!*\n\n👤 {م.first_name}\n🔗 {ي}\n🆔 `{م.id}`\n🏘 `{chat_id}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ فعّل", callback_data=f"activate_{م.id}_{chat_id}"), InlineKeyboardButton("❌ ارفض", callback_data=f"reject_{م.id}_{chat_id}")]]))
                except: pass
                await query.edit_message_text(
                    f"🤖 *اشتراك AI*\n\n💰 {سعر_نص}\n\n📱 *فودافون كاش:*\n`{VODAFONE_NUMBER}`\n\nبعد الدفع تواصل مع {OWNER_USERNAME}\n\n✅ تم إرسال طلبك!",
                    parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=f"myjrp_{chat_id}")]])
                )
        return


# ==================== File & Message Handlers ====================
async def معالج_الملفات(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ش = update.effective_chat
    م = update.effective_user
    document = update.message.document
    if not document or not document.file_name.endswith(('.xlsx', '.xls')):
        return

    if ش.type == "private":
        if not context.user_data.get('انتظر_ملف_من_خاص'):
            جروبات = await جيب_جروبات_المستخدم(م.id) if م.id != OWNER_ID else await جيب_كل_الجروبات()
            if not جروبات:
                await update.message.reply_text("❌ مفيش جروبات. ضيف البوت في جروبك الأول.")
                return
            context.user_data['ملف_معلق'] = document.file_id
            await update.message.reply_text("📚 *اختار الجروب:*", parse_mode="Markdown", reply_markup=قائمة_اختيار_جروب_للأسئلة(جروبات))
            return
        chat_id = context.user_data.get('chat_id_أسئلة')
        if not chat_id:
            await update.message.reply_text("❌ اختار الجروب الأول.")
            return
        context.user_data['انتظر_ملف_من_خاص'] = False
    else:
        if not await هو_ادمن(update, context):
            await update.message.reply_text("❌ للأدمن فقط.")
            return
        chat_id = ش.id
        context.user_data['chat_id_أسئلة'] = chat_id

    await update.message.reply_text("⏳ جاري قراءة الأسئلة...")
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    أسئلة = قراءة_أسئلة(bytes(file_bytes))
    if أسئلة:
        جيب_بيانات_جروب(chat_id)["أسئلة"] = أسئلة
        context.user_data['انتظر_مادة'] = True
        context.user_data['chat_id_أسئلة'] = chat_id
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

    if not في_الخاص:
        await تسجيل_جروب_تلقائي(ش.id, ش.title, context)

    # ===== سوبر أدمن =====
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

        if context.user_data.get("انتظر_سعر"):
            context.user_data["انتظر_سعر"] = False
            match = re.match(r'(\d+)\s*(.*)', نص)
            if match:
                سعر_الاشتراك["قيمة"] = int(match.group(1))
                سعر_الاشتراك["العملة"] = match.group(2).strip() or "جنيه"
                await update.message.reply_text(f"✅ تم تحديد السعر: *{سعر_الاشتراك['قيمة']} {سعر_الاشتراك['العملة']}/شهر*", parse_mode="Markdown", reply_markup=قائمة_سوبر_أدمن())
            else:
                await update.message.reply_text("❌ مثال: `50 جنيه`", reply_markup=قائمة_سوبر_أدمن())
            return

        match = re.match(r'تفعيل (\d+) (-?\d+)', نص)
        if match:
            uid, cid = int(match.group(1)), int(match.group(2))
            if await فعّل_ai(uid, cid):
                try: await context.bot.send_message(uid, "🎉 *تم تفعيل AI!*", parse_mode="Markdown")
                except: pass
                await update.message.reply_text("✅ تم التفعيل")
            else:
                await update.message.reply_text("❌ فشل")
            return

        match = re.match(r'وقف_ai (-?\d+)', نص)
        if match:
            await وقف_ai(int(match.group(1)))
            await update.message.reply_text("✅ تم وقف AI")
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
        context.user_data['انتظر_وقت'] = False
        ابدأ_معسكر(context, chat_id, بيانات_جروب["info"]["اسم_المادة"], دقائق, len(بيانات_جروب["أسئلة"]))
        await update.message.reply_text(f"🏕️ *المعسكر جاهز!*\n\n📚 {بيانات_جروب['info']['اسم_المادة']}\n⏱️ سؤال كل {دقائق} دقيقة\n\nسيبدأ خلال ثواني 🚀", parse_mode="Markdown")
        return

    # ===== فلتر =====
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
                await update.message.reply_text(f"🔓 تم فك الحظر.")
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

    # ===== AI =====
    اتذكر = اسم_البوت.lower() in نص.lower()
    فيه_سؤال = "؟" in نص or "?" in نص

    if (في_الخاص or اتذكر or فيه_سؤال):
        if not في_الخاص and not await ai_مفعل_للجروب(ش.id):
            if اتذكر or فيه_سؤال:
                await update.message.reply_text(f"🤖 الذكاء الاصطناعي للمشتركين فقط 💎\nتواصل مع {OWNER_USERNAME}", parse_mode="Markdown")
            return
        س = نص.replace(اسم_البوت, "").strip()
        if not س: return
        await context.bot.send_chat_action(ش.id, "typing")
        رد = await اسأل_ai(س)
        await update.message.reply_text(رد)
