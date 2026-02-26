import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

with open("models_log.txt", "w") as f:
    try:
        f.write("Available models:\n")
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                f.write(f"{m.name}\n")
    except Exception as e:
        f.write(f"Error listing models: {str(e)}\n")
