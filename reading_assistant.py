from google import genai

# To automatically pick up GEMIN_API_KEY from .env
from dotenv import load_dotenv
load_dotenv(override=True)

import os
from google.genai import types, errors
import requests

# need "Authorization: Bearer {api_key}" to query Parley
api_key = os.environ["GEMINI_API_KEY"]
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        base_url=os.environ["GOOGLE_GEMINI_BASE_URL"],
        api_version="v1",
        headers={"Authorization": f"Bearer {api_key}"},
    ),
)

r = requests.get(
    f"{os.environ['GOOGLE_GEMINI_BASE_URL']}/v1/models",
    headers={"Authorization": f"Bearer {api_key}"},
)
# print([m["id"] for m in r.json()["data"]])

prompt = 'Say hello'
model ='gemini-3.5-flash'
availableModels = os.environ.get('availableModels').split(',')

if model in availableModels:
    try:
        resp = requests.post(
                f"{os.environ['GOOGLE_GEMINI_BASE_URL']}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
        )
        resp.raise_for_status()
        print(resp.json()["choices"][0]["message"]["content"])
    except NameError:
         print(f'Select a model from [{availableModels}]')
else:
    print(f'Select a model from [{availableModels}]')
