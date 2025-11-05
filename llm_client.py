
import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAI()

    def generate_text(prompt: str, max_tokens: int = 400, model: str = 'gpt-4') -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY not set in environment')
        resp = client.chat.completions.create(
            model=model,
            messages=[{'role':'user','content':prompt}],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()

    def generate_chat(messages, max_tokens=400, model='gpt-4'):
        if not OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY not set in environment')
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()

except Exception:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY

    def generate_text(prompt: str, max_tokens: int = 400, model: str = 'gpt-4') -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY not set in environment')
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return resp['choices'][0]['message']['content'].strip()

    def generate_chat(messages, max_tokens=400, model='gpt-4'):
        if not OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY not set in environment')
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return resp['choices'][0]['message']['content'].strip()
