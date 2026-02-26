import os
import sqlite3
import struct
import subprocess
import time
import webbrowser
from urllib.parse import quote
import eel
import pvporcupine
import pyaudio
import pyautogui
import psutil
import requests
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from engine.command import speak
from engine.config import ASSISTANT_NAME
import pywhatkit as kit
from dotenv import load_dotenv

load_dotenv()

from engine.helper import extract_yt_term, remove_words


# --- Globals / DB ---
# Bug #3 fix: use absolute path for jarvis.db so multiprocessing doesn't break
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_BASE_DIR, "jarvis.db")
con = sqlite3.connect(_DB_PATH, check_same_thread=False)
cursor = con.cursor()

# WhatsApp URIs
WHATSAPP_STORE_URI = r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
WHATSAPP_PROTOCOL = "whatsapp:"


# --- Sounds ---
# Bug #9 fix: lazy-init pygame mixer (only when actually playing sound)
_pygame_inited = False


@eel.expose
def playAssistantSound():
    global _pygame_inited
    import pygame

    if not _pygame_inited:
        pygame.mixer.init()
        _pygame_inited = True

    music_dir = os.path.join(
        _BASE_DIR, "www", "assets", "vendore", "texllate", "audio", "sounds.mpeg"
    )
    try:
        pygame.mixer.music.load(music_dir)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Sound error (non-critical): {e}")


# --- Open Command ---
# Bug #2 fix: app aliases for common multi-word names Windows doesn't recognise
APP_ALIASES = {
    "vs code": "code",
    "visual studio code": "code",
    "file explorer": "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "command prompt": "cmd",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "calculator": "calc",
    "snipping tool": "snippingtool",
    "settings": "ms-settings:",
    "store": "ms-windows-store:",
    "photos": "ms-photos:",
    "camera": "microsoft.windows.camera:",
    "calendar": "outlookcal:",
    "whatsapp": "whatsapp:",
    "vlc": "vlc",
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
}

# Words that indicate the query is a sentence, NOT an app name
_SENTENCE_WORDS = {
    "and",
    "then",
    "by",
    "from",
    "mark",
    "date",
    "schedule",
    "after",
    "before",
    "during",
}

# Known websites — auto-map to https://www.<name>.com
KNOWN_SITES = {
    "google",
    "youtube",
    "github",
    "gmail",
    "facebook",
    "instagram",
    "twitter",
    "linkedin",
    "reddit",
    "wikipedia",
    "amazon",
    "netflix",
    "spotify",
    "whatsapp",
    "stackoverflow",
    "pinterest",
    "quora",
    "medium",
    "twitch",
    "discord",
}


def openCommand(query):
    # Bug #6 fix: do NOT strip 'open' again — router already did it
    query = query.replace(ASSISTANT_NAME, "")
    app_name = " ".join(query.lower().split())  # clean whitespace only

    if not app_name:
        speak("What would you like me to open?")
        return

    # --- SENTENCE GUARD ---
    words = app_name.split()
    has_sentence_words = bool(set(words) & _SENTENCE_WORDS)
    if len(words) > 3 and has_sentence_words:
        speak("I'm not sure what to open. Could you say just the app or website name?")
        return

    try:
        # 0) Check app aliases first (Bug #2 fix: "vs code" → "code")
        if app_name in APP_ALIASES:
            speak("Opening " + app_name)
            os.system(f'start "" "{APP_ALIASES[app_name]}"')
            return

        # 1) DB: local app path
        cursor.execute("SELECT path FROM sys_command WHERE name = ?", (app_name,))
        results = cursor.fetchall()
        if results:
            speak("Opening " + app_name)
            os.startfile(results[0][0])
            return

        # 2) DB: web URL
        cursor.execute("SELECT url FROM web_command WHERE name = ?", (app_name,))
        results = cursor.fetchall()
        if results:
            speak("Opening " + app_name)
            webbrowser.open(results[0][0])
            return

        # 3) Known websites
        if app_name in KNOWN_SITES:
            speak("Opening " + app_name)
            webbrowser.open(f"https://www.{app_name}.com")
            return

        # 4) WhatsApp (Custom logic: try protocol, then store)
        if app_name == "whatsapp":
            speak("Opening WhatsApp")
            # Try protocol first (often better for Desktop app)
            res = os.system(f'start "" "{WHATSAPP_PROTOCOL}"')
            if res != 0:
                os.system(f'start "" "{WHATSAPP_STORE_URI}"')
            return

        # 5) URL (has a dot like 'instagram.com')
        if any(
            ext in app_name for ext in [".com", ".in", ".org", ".net", ".io", ".co"]
        ):
            speak("Opening " + app_name)
            url = app_name if app_name.startswith("http") else "https://" + app_name
            webbrowser.open(url)
            return

        # Bug #2 fix: ALWAYS use quoted start command to handle spaces properly
        # "start" needs an empty title ("") before the actual program name
        speak("Opening " + app_name)
        result = os.system(f'start "" "{app_name}"')
        if result != 0:
            speak(f"I couldn't find {app_name}. Make sure it's installed.")

    except Exception as e:
        print(f"[openCommand error] {app_name}: {e}")
        speak("I couldn't open that. Please try again with just the app name.")


# --- System Control ---
# Bug #5 fix: added missing handlers for louder, quieter, lock
def systemControl(query):
    query = query.lower()
    if "shutdown" in query or "shut down" in query:
        speak("Are you sure you want to shutdown?")
        speak(
            "Shutdown command received. I have commented it out for safety during setup."
        )
    elif "restart" in query or "reboot" in query:
        speak("Restarting the system.")
        # os.system("shutdown /r /t 10")
    elif "sleep" in query or "hibernate" in query:
        speak("Putting the system to sleep.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif any(
        w in query for w in ["volume up", "increase volume", "louder", "turn up volume"]
    ):
        speak("Increasing volume")
        for _ in range(5):
            pyautogui.press("volumeup")
    elif any(
        w in query
        for w in ["volume down", "decrease volume", "quieter", "turn down volume"]
    ):
        speak("Decreasing volume")
        for _ in range(5):
            pyautogui.press("volumedown")
    elif "mute" in query or "unmute" in query or "silence" in query:
        speak("Toggling mute")
        pyautogui.press("volumemute")
    elif "lock" in query:
        speak("Locking the screen")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        speak("I didn't understand that system command.")


# --- Web Automation ---
def webAutomation(query):
    query = query.lower()
    if "gmail" in query:
        if "type" in query or "compose" in query or "send" in query or "write" in query:
            for kw in ["type", "compose", "send", "write"]:
                if kw in query:
                    message = query.split(kw, 1)[-1].strip()
                    break
            else:
                message = ""

            speak("Opening Gmail compose window.")
            webbrowser.open("https://mail.google.com/mail/u/0/#inbox?compose=new")
            time.sleep(6)

            if message:
                pyautogui.write(message, interval=0.07)
                speak("Done! I have typed your message.")
            else:
                speak("Compose window is open. You can type your message now.")
        else:
            speak("Opening Gmail.")
            webbrowser.open("https://mail.google.com/mail/u/0/#inbox")

    elif any(
        word in query
        for word in [
            "type an email",
            "compose an email",
            "send an email",
            "write an email",
            "new email",
            "compose email",
        ]
    ):
        speak("Opening Gmail compose window.")
        webbrowser.open("https://mail.google.com/mail/u/0/#inbox?compose=new")
        time.sleep(6)
        speak("Compose window is open. Please type your message or say it.")

    elif "search" in query:
        search_query = query.replace("search", "").strip()
        speak(f"Searching for {search_query}")
        webbrowser.open(f"https://www.google.com/search?q={search_query}")


# --- Advanced Capabilities ---
def typeCommand(message):
    """Type text into the active window."""
    if not message:
        speak("What should I type?")
        from engine.command import takecommand

        message = takecommand()

    if message:
        speak("Typing now.")
        # interval makes it look more natural/robotic but prevents overflow
        pyautogui.write(message, interval=0.04)
        speak("Done.")


def cameraCommand():
    """Launch the camera application."""
    speak("Opening camera.")
    os.system('start "" "microsoft.windows.camera:"')


# --- Proactive Intelligence ---
def systemInfo():
    cpu = psutil.cpu_percent(interval=1)
    battery = psutil.sensors_battery()

    status_msg = f"Sir, the CPU is currently operating at {cpu} percent."
    if battery:
        plugged = "plugged in" if battery.power_plugged else "not plugged in"
        status_msg += (
            f" The system battery is at {battery.percent} percent and is {plugged}."
        )

    speak(status_msg)


def morningBriefing():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        speak("Good Morning Sir!")
    elif hour >= 12 and hour < 18:
        speak("Good Afternoon Sir!")
    else:
        speak("Good Evening Sir!")

    speak("Here is your briefing.")

    # Weather
    try:
        ip_response = requests.get("http://ip-api.com/json/").json()
        city = ip_response.get("city", "your city")
        lat = ip_response.get("lat", 28.61)
        lon = ip_response.get("lon", 77.23)

        weather_response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()
        temp = weather_response["current_weather"]["temperature"]

        speak(
            f"You are currently in {city}. The temperature outside is {temp} degrees Celsius."
        )
    except Exception:
        speak("I couldn't fetch the weather information currently.")

    # News
    try:
        url = "https://news.google.com/rss"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req)
        xml_page = response.read()

        root = ET.fromstring(xml_page)
        headlines = []
        for item in root.findall("./channel/item")[:3]:
            headlines.append(item.find("title").text)

        speak("Here are the top news headlines.")
        for i, h in enumerate(headlines):
            speak(f"Headline {i+1}: {h}")
    except Exception:
        speak("I couldn't fetch the news right now.")


# --- YouTube ---
def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:
        speak("Playing " + search_term + " on Youtube")
        kit.playonyt(search_term)
    else:
        speak("I could not understand what to play on Youtube")


# --- Hotword ---
def hotword(jarvis_busy=None, hotword_triggered=None):
    porcupine = None
    paud = None
    audio_stream = None
    try:
        access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        porcupine = pvporcupine.create(
            access_key=access_key, keywords=["jarvis", "alexa"]
        )
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        while True:
            # Bug #1 fix: if Jarvis main process is busy, skip detection entirely
            if jarvis_busy and jarvis_busy.is_set():
                time.sleep(0.3)
                continue

            keyword = audio_stream.read(
                porcupine.frame_length, exception_on_overflow=False
            )
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("hotword detected")

                if hotword_triggered:
                    # Signal main process to start listening
                    hotword_triggered.set()
                else:
                    # Fallback for old run methods (not recommended)
                    pyautogui.keyDown("win")
                    pyautogui.press("j")
                    time.sleep(0.2)
                    pyautogui.keyUp("win")

                # DEBOUNCE: destroy & recreate audio stream after cooldown
                audio_stream.close()
                paud.terminate()
                porcupine.delete()

                print("[hotword] cooling down 7s...")
                time.sleep(7)

                access_key = os.getenv("PICOVOICE_ACCESS_KEY")
                porcupine = pvporcupine.create(
                    access_key=access_key, keywords=["jarvis", "alexa"]
                )
                paud = pyaudio.PyAudio()
                audio_stream = paud.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length,
                )

    except Exception as e:
        print("Hotword Error:", e)

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
        "whatsapp",
        "wahtsapp",
        "video",
        "type",
        "greeting",
        "on",
        "tell",
        "open",
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
        if not mobile_number_str.startswith("+91"):
            mobile_number_str = "+91" + mobile_number_str
        return mobile_number_str, q
    except Exception:
        return 0, 0


# --- WhatsApp ---
def whatsApp(mobile_no, message, flag, name, auto_send=True):
    if flag == "message":
        jarvis_message = f"Opening chat with {name} and drafting your message."
    elif flag == "call":
        jarvis_message = f"Starting a WhatsApp voice call to {name}."
    else:
        jarvis_message = f"Starting a WhatsApp video call to {name}."

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    speak(jarvis_message)
    os.system(f'start "" "{whatsapp_url}"')

    # wait for WhatsApp to open/focus
    time.sleep(4)

    if flag == "message" and auto_send:
        pyautogui.press("enter")
        speak("Message sent successfully.")
    elif flag == "message" and not auto_send:
        speak("I have typed the message for you.")
    elif flag == "call":
        # Automation: Start Voice Call
        pyautogui.hotkey("ctrl", "shift", "c")
        speak("Call started.")
    elif flag == "video call":
        # Automation: Start Video Call
        pyautogui.hotkey("ctrl", "shift", "v")
        speak("Video call started.")


def whatsAppSearch(name, flag, message=None, auto_send=True):
    """Fully Automated Fallback: Search and Action."""
    # Open WhatsApp
    os.system('start "" "whatsapp:"')
    time.sleep(3)

    # Focus search bar
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.5)

    # Type name slowly
    pyautogui.write(name, interval=0.1)
    time.sleep(3)

    # Press Enter to open chat
    pyautogui.press("enter")
    time.sleep(2)

    if flag == "message" and message:
        pyautogui.write(message, interval=0.04)
        if auto_send:
            time.sleep(0.5)
            pyautogui.press("enter")
            speak(f"Message sent to {name}.")
        else:
            speak(f"Message typed for {name}.")
    elif flag == "call":
        pyautogui.hotkey("ctrl", "shift", "c")
        speak(f"Voice call started for {name}.")
    elif flag == "video call":
        pyautogui.hotkey("ctrl", "shift", "v")
        speak(f"Video call started for {name}.")
