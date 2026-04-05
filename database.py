import logging
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


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
            supabase.table("جروبات").insert({
                "chat_id": chat_id, "اسم": اسم, "owner_id": owner_id,
                "عدد_الأعضاء": 0, "تاريخ_الإضافة": "now()"
            }).execute()
            logging.info(f"✅ تم تسجيل جروب: {chat_id} owner: {owner_id}")
        else:
            supabase.table("جروبات").update({"اسم": اسم, "owner_id": owner_id}).eq("chat_id", chat_id).execute()
    except Exception as ex:
        logging.error(f"سجل_جروب ERROR: {ex}")

async def جيب_جروبات_المستخدم(user_id):
    if not supabase: return []
    try:
        r = supabase.table("جروبات").select("*").eq("owner_id", user_id).execute()
        return r.data or []
    except: return []

async def جيب_كل_الجروبات():
    if not supabase: return []
    try:
        r = supabase.table("جروبات").select("*").execute()
        return r.data or []
    except: return []

async def جيب_owner_id(chat_id):
    if not supabase: return None
    try:
        r = supabase.table("جروبات").select("owner_id").eq("chat_id", chat_id).execute()
        return r.data[0]["owner_id"] if r.data else None
    except: return None

async def ai_مفعل_للجروب(chat_id):
    if not supabase: return False
    try:
        r = supabase.table("اشتراكات").select("ai_مفعل").eq("chat_id", chat_id).execute()
        return bool(r.data[0]["ai_مفعل"]) if r.data else False
    except: return False

async def فعّل_ai(user_id, chat_id):
    if not supabase: return False
    try:
        e = supabase.table("اشتراكات").select("id").eq("chat_id", chat_id).execute()
        if e.data:
            supabase.table("اشتراكات").update({"ai_مفعل": True, "user_id": user_id}).eq("chat_id", chat_id).execute()
        else:
            supabase.table("اشتراكات").insert({"user_id": user_id, "chat_id": chat_id, "ai_مفعل": True}).execute()
        logging.info(f"✅ تم تفعيل AI للجروب: {chat_id}")
        return True
    except Exception as ex:
        logging.error(f"فعّل_ai ERROR: {ex}")
        return False

async def وقف_ai(chat_id):
    if not supabase: return False
    try:
        supabase.table("اشتراكات").update({"ai_مفعل": False}).eq("chat_id", chat_id).execute()
        return True
    except: return False

async def جيب_طلبات_الاشتراك():
    if not supabase: return []
    try:
        r = supabase.table("اشتراكات").select("*").eq("ai_مفعل", False).execute()
        return r.data or []
    except: return []

async def جيب_مشتركين_ai():
    if not supabase: return []
    try:
        r = supabase.table("اشتراكات").select("*").eq("ai_مفعل", True).execute()
        return r.data or []
    except: return []

async def جيب_إحصائيات():
    if not supabase: return {}
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
    except: return {}

async def سجل_طلب_اشتراك(user_id, chat_id, الاسم):
    if not supabase: return
    try:
        e = supabase.table("اشتراكات").select("id").eq("user_id", user_id).eq("chat_id", chat_id).execute()
        if not e.data:
            supabase.table("اشتراكات").insert({"user_id": user_id, "chat_id": chat_id, "الاسم": الاسم, "ai_مفعل": False}).execute()
    except: pass
