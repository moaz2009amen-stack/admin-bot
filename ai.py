import os
import logging
from groq import Groq
from config import اسم_الصانع

GROQ_KEY = os.environ.get("GROQ_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

SYSTEM_PROMPT = f"""أنت مساعد ذكي متخصص في مساعدة الطلاب على المذاكرة، اسمك بووووو وصنعك {اسم_الصانع}.
قواعدك:
- تتكلم بالعامية المصرية دايماً
- متخصص في شرح المناهج الدراسية
- لو حد سألك سؤال دراسي: اشرحه بأسلوب بسيط وأمثلة
- لو حد طلب تلخيص: لخص بنقاط واضحة
- لو حد عايز أسئلة تدريبية: اعمله أسئلة مع الإجابات
- لو حد سألك مين صنعك: قوله {اسم_الصانع}
- ردودك خفيفة وودودة وتشجع على المذاكرة"""

async def اسأل_ai(سؤال: str) -> str:
    if not groq_client:
        logging.error("GROQ_KEY مش موجود!")
        return "❌ الـ AI مش متاح دلوقتي."
    try:
        رد = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": سؤال}
            ]
        )
        return رد.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Groq error: {e}")
        return "❌ في مشكلة في الاتصال، جرب تاني."
