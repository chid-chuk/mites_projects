import os
from google import genai
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
client = create_client(api_key(), availableModels=availableModels, timeout_s = 10)

print('Available models are:', client._availableModels())

model ='gemini-2.5-flash-image'
prompt = 'Generate a picture of a cat'
image = client.interact(model, prompt, choice=2)


from PIL import Image

# 1. Convert base64 to byte stream
if type(image) != bytes:
    image = image.data

# 2. Save and display the image
with open("generated_image.png", "wb") as f:
    f.write(image)

# 3. Open and display with your system's default viewer
img = Image.open(fp="generated_image.png")
img.show()
