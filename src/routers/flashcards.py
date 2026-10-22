from fastapi import APIRouter, HTTPException
from src.schemas.flashcard import FlashcardRequest
from src.services.groq_service import generate_llm_json

router = APIRouter(
    prefix="/api/v1/flashcards",
    tags=["Phase 2: Flashcards"]
)

SYSTEM_PROMPT = """أنت خبير تربوي متخصص في علوم الحديث النبوي الشريف وتصميم البطاقات التعليمية (Flashcards) لنظام التكرار المتباعد (Spaced Repetition).
مهمتك هي توليد بطاقات تعليمية دقيقة باللغة العربية الفصحى بالاعتماد حصرياً على (نص الحديث، والراوي، والشرح المعتمد) المرفقين لك.
ممنوع منعاً باتاً اختلاق أي معلومات أو معاني غير موجودة في النص المرفق.
في بطاقات إكمال الفراغ، احذف الكلمة كاملة بحروف الجر المتصلة بها ولا تفصل الكلمة الواحدة.

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

@router.post("/generate")
async def generate_flashcards(request: FlashcardRequest):
    user_prompt = f"""قم بتوليد عدد ({request.num_cards}) بطاقات تعليمية (Flashcards) من المحتوى الموثوق التالي:

- نص الحديث: {request.hadith_text}
- راوي الحديث: {request.narrator if request.narrator else "غير محدد"}
- الشرح والمعاني المعتمدة: {request.explanation}

أخرج النتيجة بصيغة JSON فقط مطابقة للهيكل المطلوب."""

    try:
        parsed_json = await generate_llm_json(SYSTEM_PROMPT, user_prompt, temperature=0.2)
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