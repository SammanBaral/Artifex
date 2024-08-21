import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure the generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def generate_ai_response(text):
    response = chat.send_message(text, stream=True)
    ai_response = ""
    for chunk in response:
        ai_response += chunk.text
    return ai_response.strip()