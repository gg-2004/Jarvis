import sqlite3
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

with open("diag_log.txt", "w") as f:
    f.write("--- DB CHECK ---\n")
    if os.path.exists("jarvis.db"):
        conn = sqlite3.connect("jarvis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        f.write(f"Tables: {tables}\n")
        for table in tables:
            t_name = table[0]
            cursor.execute(f"PRAGMA table_info({t_name});")
            info = cursor.fetchall()
            f.write(f"Schema for {t_name}: {info}\n")

            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
            count = cursor.fetchone()[0]
            f.write(f"Rows in {t_name}: {count}\n")
        conn.close()
    else:
        f.write("jarvis.db NOT FOUND\n")

    f.write("\n--- GEMINI CHECK ---\n")
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Say 'Gemini OK'")
            f.write(f"Response: {response.text}\n")
        except Exception as e:
            f.write(f"Gemini Error: {str(e)}\n")
    else:
        f.write("GEMINI_API_KEY NOT FOUND\n")

    f.write("\n--- PICO CHECK ---\n")
    pico_key = os.getenv("PICOVOICE_ACCESS_KEY")
    f.write(f"PICO_KEY Length: {len(pico_key) if pico_key else 'None'}\n")
