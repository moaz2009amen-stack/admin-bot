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
- ردودك تكون مفيدة وخفيفة وتشجع على المذاكرة"""

# نجرب أكتر من موديل لو واحد فشل
MODELS = [
    "deepseek/deepseek-chat-v3-0324:free",
    "deepseek/deepseek-r1:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
]

async def اسأل_ai(سؤال: str) -> str:
    if not OPENROUTER_KEY:
        logging.error("OPENROUTER_KEY مش موجود!")
        return "❌ الـ AI مش متاح دلوقتي."

    for model in MODELS:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://t.me",
                        "X-Title": "بووووو بوت",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": سؤال}
                        ],
                        "max_tokens": 1000,
                    }
                )
                data = r.json()
                logging.info(f"OpenRouter response ({model}): {r.status_code}")

                if "choices" in data and data["choices"]:
                    رد = data["choices"][0]["message"]["content"]
                    if رد and رد.strip():
                        return رد.strip()

                # لو في error ف الـ response
                if "error" in data:
                    logging.warning(f"Model {model} error: {data['error']}")
                    continue

        except Exception as e:
            logging.error(f"AI error ({model}): {e}")
            continue

    return "❌ مش قادر أجاوب دلوقتي، جرب تاني بعد شوية."
