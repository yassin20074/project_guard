import os
import json
import httpx
from fastapi import HTTPException

def get_groq_api_key() -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the server.")
    return api_key

async def transcribe_audio_groq(filename: str, audio_bytes: bytes, content_type: str) -> str:
    api_key = get_groq_api_key()
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
            detail=f"Groq Whisper API Error: {response.text}"
        )

    result_json = response.json()
    return result_json.get("text", "").strip()

async def generate_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    api_key = get_groq_api_key()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature
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
    return json.loads(content_str)
