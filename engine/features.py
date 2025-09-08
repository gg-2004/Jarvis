import os
import sqlite3
import struct
import subprocess
import time
import webbrowser
from urllib.parse import quote  # URL-safe percent-encoding
from playsound import playsound
import eel
import pvporcupine
import pyaudio
import pyautogui
from engine.command import speak
from engine.config import ASSISTANT_NAME
import pywhatkit as kit

from engine.helper import extract_yt_term, remove_words



# --- Globals / DB ---
con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

# WhatsApp (Microsoft Store) App URI
WHATSAPP_APP_URI = r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"


# --- Sounds ---
@eel.expose
def playAssistantSound():
    music_dir = r"www\assets\vendore\texllate\audio\sounds.mpeg"
    playsound(music_dir)


# --- Open Command ---
def openCommand(query):
    # normalize user text
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query = query.lower().strip()

    app_name = query
    if app_name == "":
        return

    try:
        # 1) Try local app path mapping from DB
        cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
        results = cursor.fetchall()

        if len(results) != 0:
            speak("Opening " + app_name)
            os.startfile(results[0][0])
            return

        # 2) Try web URL mapping from DB
        cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (app_name,))
        results = cursor.fetchall()
        if len(results) != 0:
            speak("Opening " + app_name)
            webbrowser.open(results[0][0])
            return

        # 3) Special case for WhatsApp (Microsoft Store)
        if "whatsapp" in app_name:
            speak("Opening WhatsApp")
            os.system("start " + WHATSAPP_APP_URI)
            return

        # 4) Fallback to Win+R "start <name>"
        speak("Opening " + app_name)
        os.system("start " + app_name)

    except Exception:
        speak("something went wrong")


# --- YouTube ---
def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:  # only if regex found something
        speak("Playing " + search_term + " on Youtube")
        kit.playonyt(search_term)
    else:
        speak("I could not understand what to play on Youtube")


# --- Hotword ---
def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        # pre trained keywords
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        # loop for streaming
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

            # processing keyword detected for mic
            keyword_index = porcupine.process(keyword)

            # checking first keyword detected or not
            if keyword_index >= 0:
                print("hotword detected")

                # pressing shortcut key win+j
                pyautogui.keyDown("win")
                pyautogui.press("j")
                time.sleep(2)
                pyautogui.keyUp("win")  # fixed stray space

    except Exception as e:
        print("Error:", e)
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


# --- Contacts ---
def findContact(query):
    words_to_remove = [
        "make",
        "a",
        "to",
        "phone",
        "call",
        "send",
        "message",
        "wahtsapp",
        "video",
    ]
    query = remove_words(query, words_to_remove)

    try:
        q = query.strip().lower()
        cursor.execute(
            "SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ("%" + q + "%", q + "%"),
        )
        results = cursor.fetchall()
        mobile_number_str = str(results[0][0])
        if not mobile_number_str.startswith('+91'):
            mobile_number_str = '+91' + mobile_number_str
        return mobile_number_str, q
    except Exception:
        speak('not exist in contacts')
        return 0, 0


# --- WhatsApp ---
def whatsApp(mobile_no, message, flag, name):
    if flag == 'message':
        jarvis_message = "Message sent successfully to " + name
    elif flag == 'call':
        jarvis_message = "I have opened WhatsApp, please click the call button for " + name
    else:  # video call
        jarvis_message = "I have opened WhatsApp, please click the video call button for " + name

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Open WhatsApp Desktop chat
    os.system(f'start "" "{whatsapp_url}"')

    # Auto-send only for text messages
    if flag == 'message':
        time.sleep(1)
        pyautogui.press('enter')

    speak(jarvis_message)


