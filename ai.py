import httpx
import logging
from config import OPENROUTER_KEY, اسم_الصانع

SYSTEM_PROMPT = f"""أنت مساعد ذكي متخصص في مساعدة الطلاب على المذاكرة، اسمك بووووو وصنعك {اسم_الصانع}.

قواعدك:
- تتكلم بالعامية المصرية دايماً
- متخصص في شرح المناهج الدراسية
- لو حد سألك سؤال دراسي: اشرحه بأسلوب بسيط وأمثلة
- لو حد طلب تلخيص: لخص بنقاط واضحة
- لو حد عايز أسئلة: اعمله أسئلة مع الإجابات
- لو حد سألك مين صنعك: قوله {اسم_الصانع}
- ردودك تكون مفيدة وخفيفة وتشجع على المذاكرة
"""

async def اسأل_ai(سؤال: str) -> str:
    if not OPENROUTER_KEY:
        return "❌ الـ AI مش متاح دلوقتي."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://t.me/bot",
                },
                json={
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": سؤال}
                    ],
                    "max_tokens": 1000,
                }
            )
            data = r.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            logging.error(f"OpenRouter response: {data}")
            return "❌ مش قادر أجاوب دلوقتي، جرب تاني."
    except Exception as e:
        logging.error(f"AI error: {e}")
        return "❌ في مشكلة في الاتصال، جرب تاني."
