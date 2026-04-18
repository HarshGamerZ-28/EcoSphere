import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv('../.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

async def test_gemini():
    payload = {
        'contents': [{'parts': [{'text': 'Return a JSON array with test: true'}]}],
        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 100}
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f'{GEMINI_URL}?key={GEMINI_API_KEY}', json=payload)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            print('✅ Gemini API connection successful!')
            data = resp.json()
            print(f'Response: {data["candidates"][0]["content"]["parts"][0]["text"]}')
        else:
            print(f'❌ Error: {resp.text}')

asyncio.run(test_gemini())
