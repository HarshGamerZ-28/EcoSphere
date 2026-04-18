import httpx
import json
import asyncio

GEMINI_API_KEY = "AIzaSyA8URkJ0bE38QXkIs8MC5keikJbWL-yZKk"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def test_key():
    payload = {
        'contents': [{'parts': [{'text': 'Hello'}]}],
        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 100}
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f'{GEMINI_URL}?key={GEMINI_API_KEY}', json=payload)
        print(f'Status: {resp.status_code}')
        print(f'Response:\n{json.dumps(resp.json(), indent=2)}')

asyncio.run(test_key())
