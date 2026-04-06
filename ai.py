import os
import httpx
import logging
from config import اسم_الصانع

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY")

SYSTEM_PROMPT = f"""أنت مساعد ذكي متخصص في مساعدة الطلاب على المذاكرة، اسمك بووووو وصنعك {اسم_الصانع}.
قواعدك:
- تتكلم بالعامية المصرية دايماً
- متخصص في شرح المناهج الدراسية
- لو حد سألك سؤال دراسي: اشرحه بأسلوب بسيط وأمثلة
- لو حد طلب تلخيص: لخص بنقاط واضحة
- لو حد عايز أسئلة: اعمله أسئلة مع الإجابات
- لو حد سألك مين صنعك: قوله {اسم_الصانع}
- ردودك تكون مفيدة وخفيفة وتشجع على المذاكرة"""

async def اسأل_ai(سؤال: str) -> str:
    if not DEEPSEEK_KEY:
        logging.error("DEEPSEEK_KEY مش موجود!")
        return "❌ الـ AI مش متاح دلوقتي."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": سؤال}
                    ],
                    "max_tokens": 1000,
                }
            )
            data = r.json()
            logging.info(f"Deepseek status: {r.status_code}")
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"].strip()
            logging.error(f"Deepseek error: {data}")
            return "❌ مش قادر أجاوب دلوقتي، جرب تاني."
    except Exception as e:
        logging.error(f"Deepseek error: {e}")
        return "❌ في مشكلة في الاتصال، جرب تاني."
