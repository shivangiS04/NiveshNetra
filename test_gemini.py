import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path('.env'))
key = os.environ.get('GEMINI_API_KEY', 'NOT FOUND')
print('KEY:', key[:10] + '...' if len(key) > 10 else key)

import google.generativeai as genai
genai.configure(api_key=key)
m = genai.GenerativeModel('gemini-1.5-flash')
r = m.generate_content('Say hello in 5 words')
print('Response:', r.text)
