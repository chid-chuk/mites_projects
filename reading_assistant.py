import os
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv
from gemini_client import create_client

# To automatically pick up GEMIN_API_KEY from .env
load_dotenv(override=True)

# For Parley API
# def api_key():
#     ''' Function to pull api key '''
#     return os.environ["PARLEY_API_KEY"]

# base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
# availableModels = os.environ.get('availableModels').split(',')
# client = create_client(api_key(), availableModels=availableModels, base_url=base_url)


# print(client.interact(model,prompt))

# Directly using Gemini api key (currently disfunctional)
def api_key():
    ''' Function to pull api key '''
    return os.environ["GEMINI_API_KEY"]


availableModels = os.environ.get('GEMINI_availableModels').split(',')
client = create_client(api_key(), availableModels=availableModels)

model ='gemini-3.5-flash-lite'
prompt = 'Say hello'
print(client.interact(model, prompt))
