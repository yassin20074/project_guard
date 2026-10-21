# استخدام نسخة بايثون خفيفة ومستقرة
FROM python:3.11-slim

# منع بايثون من كتابة ملفات .pyc وتفعيل الطباعة الفورية للـ Logs في Railway
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها أولاً للاستفادة من الـ Docker Cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY main.py .
Copy .dockerignore .

# فتح البورت الافتراضي
EXPOSE 8000

# تشغيل السيرفر مع قراءة متغير البورت الديناميكي الخاص بـ Railway
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
