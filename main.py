import os
import re
import difflib
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Smart Hadith Platform - AI Engine",
    description="APIs خاصة بمنصة الحديث الذكية - Phase 1: نظام التسميع الذكي",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def home():
    return {"status": "online", "message": "Smart Hadith AI API is running (Phase 1 Ready)"}

@app.post("/api/v1/recitation/check")
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

        # إرسال الطلب مباشرة لـ Groq REST API بدون الاعتماد على مكتبة groq
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        files = {
            "file": (filename, audio_bytes, content_type)
        }
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
