from typing import Optional
from pydantic import BaseModel, Field

class FlashcardRequest(BaseModel):
    hadith_text: str = Field(..., description="النص الأصلي للحديث النبوي")
    explanation: str = Field(..., description="الشرح المعتمد والموثوق للحديث ومعاني الكلمات")
    narrator: Optional[str] = Field("", description="اسم راوي الحديث ونبذة عنه (إن وجد)")
    num_cards: int = Field(5, description="عدد الفلاش كاردز المطلوب توليدها (الافتراضي 5)", ge=1, le=15)