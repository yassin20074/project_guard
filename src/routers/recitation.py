from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.services.groq_service import transcribe_audio_groq
from src.services.text_matching import compare_texts

router = APIRouter(
    prefix="/api/v1/recitation",
    tags=["Phase 1: Recitation"]
)

@router.post("/check")
async def check_recitation(
    original_hadith: str = Form(..., description="النص الأصلي للحديث للمقارنة"),
    audio_file: UploadFile = File(..., description="ملف الصوت المسجل من الطالب")
):
    try:
        audio_bytes = await audio_file.read()
        filename = audio_file.filename if audio_file.filename else "audio.ogg"
        content_type = audio_file.content_type if audio_file.content_type else "audio/ogg"

        student_text = await transcribe_audio_groq(filename, audio_bytes, content_type)
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