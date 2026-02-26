import sqlite3
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def check_db():
    print("--- checking database ---")
    if not os.path.exists("jarvis.db"):
        print("Error: jarvis.db not found")
        return
    try:
        conn = sqlite3.connect("jarvis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        for table in tables:
            t_name = table[0]
            cursor.execute(f"PRAGMA table_info({t_name});")
            info = cursor.fetchall()
            print(f"Schema for {t_name}: {info}")
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")


def check_gemini():
    print("\n--- checking gemini api ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("hello")
        print(f"Gemini Response: {response.text[:50]}...")
    except Exception as e:
        print(f"Gemini Error: {e}")


def check_assets():
    print("\n--- checking web assets ---")
    assets = ["www/index.html", "www/main.js", "www/style.css"]
    for asset in assets:
        if os.path.exists(asset):
            print(f"Asset found: {asset}")
        else:
            print(f"Asset MISSING: {asset}")


if __name__ == "__main__":
    print("DIAGNOSTIC START")
    check_db()
    check_gemini()
    check_assets()
    print("\n--- checking environment ---")
    print(f"PICO_KEY set: {bool(os.getenv('PICOVOICE_ACCESS_KEY'))}")
    print(f"GEMINI_KEY set: {bool(os.getenv('GEMINI_API_KEY'))}")
    print("DIAGNOSTIC END")
