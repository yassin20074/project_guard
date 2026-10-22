import os
import re
import json
import difflib
import httpx
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Smart Hadith Platform - AI Engine",
    description="APIs خاصة بمنصة الحديث الذكية - Phase 1 (التسميع) & Phase 2 (البطاقات التعليمية)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# نماذج البيانات (Pydantic Models) - Phase 2
# ==========================================
class FlashcardRequest(BaseModel):
    hadith_text: str = Field(..., description="النص الأصلي للحديث النبوي")
    explanation: str = Field(..., description="الشرح المعتمد والموثوق للحديث ومعاني الكلمات")
    narrator: Optional[str] = Field("", description="اسم راوي الحديث ونبذة عنه (إن وجد)")
    num_cards: int = Field(5, description="عدد الفلاش كاردز المطلوب توليدها (الافتراضي 5)", ge=1, le=15)


# ==========================================
# دوال مساعدة - Phase 1 (التسميع الذكي)
# ==========================================
def normalize_arabic(text: str) -> str:
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة\b', 'ه', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compare_texts(reference: str, recited: str):
    ref_norm = normalize_arabic(reference)
    rec_norm = normalize_arabic(recited)

    ref_words = ref_norm.split()
    rec_words = rec_norm.split()

    matcher = difflib.SequenceMatcher(None, ref_words, rec_words)
    similarity_ratio = round(matcher.ratio() * 100, 2)

    missing_words = []
    replaced_words = []
    extra_words = []
    word_by_word_analysis = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in ref_words[i1:i2]:
                word_by_word_analysis.append({"word": w, "status": "correct"})
        elif tag == 'delete':
            for w in ref_words[i1:i2]:
                missing_words.append(w)
                word_by_word_analysis.append({"word": w, "status": "missing"})
        elif tag == 'insert':
            for w in rec_words[j1:j2]:
                extra_words.append(w)
                word_by_word_analysis.append({"word": w, "status": "extra"})
        elif tag == 'replace':
            expected_chunk = " ".join(ref_words[i1:i2])
            spoken_chunk = " ".join(rec_words[j1:j2])
            replaced_words.append({
                "expected": expected_chunk,
                "spoken": spoken_chunk
            })
            word_by_word_analysis.append({
                "expected": expected_chunk,
                "spoken": spoken_chunk,
                "status": "replaced"
            })

    return {
        "similarity_percentage": similarity_ratio,
        "is_passed": similarity_ratio >= 85.0,
        "missing_words": missing_words,
        "replaced_words": replaced_words,
        "extra_words": extra_words,
        "detailed_analysis": word_by_word_analysis
    }


# ==========================================
# الـ Endpoints
# ==========================================
@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Smart Hadith AI API is running (Phase 1 & Phase 2 Ready)",
        "endpoints": [
            "/api/v1/recitation/check",
            "/api/v1/flashcards/generate"
        ]
    }


# --- Phase 1: نظام التسميع الذكي ---
@app.post("/api/v1/recitation/check", tags=["Phase 1: Recitation"])
async def check_recitation(
    original_hadith: str = Form(..., description="النص الأصلي للحديث للمقارنة"),
    audio_file: UploadFile = File(..., description="ملف الصوت المسجل من الطالب")
):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the server.")

    try:
        audio_bytes = await audio_file.read()
        filename = audio_file.filename if audio_file.filename else "audio.ogg"
        content_type = audio_file.content_type if audio_file.content_type else "audio/ogg"

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": (filename, audio_bytes, content_type)}
        data = {
            "model": "whisper-large-v3-turbo",
            "language": "ar",
            "response_format": "json",
            "temperature": "0.0"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, files=files, data=data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Groq API Error: {response.text}"
            )

        result_json = response.json()
        student_text = result_json.get("text", "").strip()
        comparison_result = compare_texts(original_hadith, student_text)

        return {
            "success": True,
            "original_hadith": original_hadith,
            "transcribed_text": student_text,
            "evaluation": comparison_result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


# --- Phase 2: توليد البطاقات التعليمية (Flashcards) ---
@app.post("/api/v1/flashcards/generate", tags=["Phase 2: Flashcards"])
async def generate_flashcards(request: FlashcardRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the server.")

    system_prompt = """أنت خبير تربوي متخصص في علوم الحديث النبوي الشريف وتصميم البطاقات التعليمية (Flashcards) لنظام التكرار المتباعد (Spaced Repetition).
مهمتك هي توليد بطاقات تعليمية دقيقة باللغة العربية الفصحى بالاعتماد حصرياً على (نص الحديث، والراوي، والشرح المعتمد) المرفقين لك.
ممنوع منعاً باتاً اختلاق أي معلومات أو معاني غير موجودة في النص المرفق.

يجب أن تتنوع البطاقات بين الأنواع الثلاثة التالية:
1. "fill_in_the_blank": بطاقات إكمال الفراغ (لاختبار استرجاع كلمات الحديث المفتاحية بوضع نقاط مكان الكلمة في وجه البطاقة، والكلمة الصحيحة في ظهر البطاقة).
2. "vocabulary_and_narrator": بطاقات الرواة والمعاني (للربط بين الكلمة ومعناها من الشرح، أو السؤال عن راوي الحديث).
3. "benefits_and_context": بطاقات الفوائد والفهم (سؤال مباشر حول فائدة أو معنى مستنبط من الشرح المرفق).

يجب أن يكون إخراجك بصيغة JSON فقط ويحتوي على المفتاح "flashcards" وبداخله قائمة من الكائنات (Objects)، كل كائن يحتوي على:
- "id": رقم البطاقة (1, 2, ...).
- "type": نوع البطاقة ("fill_in_the_blank" أو "vocabulary_and_narrator" أو "benefits_and_context").
- "type_ar": نوع البطاقة بالعربية ("إكمال الفراغ" أو "الرواة والمعاني" أو "الفوائد والفهم").
- "front": وجه البطاقة (السؤال أو العبارة التي بها فراغ).
- "back": ظهر البطاقة (الإجابة الدقيقة والمختصرة من النص المعتمد).
- "hint": تلميح بسيط لمساعدة الطالب على التذكر دون كشف الإجابة الكاملة.
"""

    user_prompt = f"""قم بتوليد عدد ({request.num_cards}) بطاقات تعليمية (Flashcards) من المحتوى الموثوق التالي:

- نص الحديث: {request.hadith_text}
- راوي الحديث: {request.narrator if request.narrator else "غير محدد"}
- الشرح والمعاني المعتمدة: {request.explanation}

أخرج النتيجة بصيغة JSON فقط مطابقة للهيكل المطلوب."""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Groq LLM Error: {response.text}"
            )

        result_data = response.json()
        content_str = result_data["choices"][0]["message"]["content"]
        parsed_json = json.loads(content_str)
        flashcards_list = parsed_json.get("flashcards", [])

        return {
            "success": True,
            "hadith_text": request.hadith_text,
            "total_generated": len(flashcards_list),
            "flashcards": flashcards_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating flashcards: {str(e)}")
