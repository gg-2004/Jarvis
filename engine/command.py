import pyttsx3
import speech_recognition as sr
import eel
import time
from google import genai
import os
import random
import re
from dotenv import load_dotenv

# ========== GEMINI SETUP ==========
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
_gemini_client = genai.Client(api_key=API_KEY)

# Rate-limit guard
_last_gemini_call = 0
_GEMINI_COOLDOWN_SECS = 4


def ask_gemini(prompt):
    global _last_gemini_call
    now = time.time()
    gap = now - _last_gemini_call
    if gap < _GEMINI_COOLDOWN_SECS:
        time.sleep(_GEMINI_COOLDOWN_SECS - gap)
    response = _gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    _last_gemini_call = time.time()
    return response.text


# Local fallback replies when Gemini is unavailable
LOCAL_FALLBACK_REPLIES = [
    "I'm having trouble reaching my AI brain right now. Please try again in a moment.",
    "My connection to the AI service is limited right now. Ask me something else or try again.",
    "I couldn't process that right now due to a quota limit. What else can I help you with?",
    "I'm temporarily offline for AI responses. I can still open apps, search the web, check system status, and more!",
]


def local_fallback():
    return random.choice(LOCAL_FALLBACK_REPLIES)


# ========== BUSY EVENT (Bug #1 fix) ==========
# Set by run.py via set_busy_event() before eel.start()
# Checked by hotword process to pause during command execution
_jarvis_busy = None


def set_busy_event(event):
    """Called by main.py at startup to wire the multiprocessing Event."""
    global _jarvis_busy
    _jarvis_busy = event


# ========== SPEAK ==========
def speak(text):
    try:
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[1].id)
        engine.setProperty("rate", 174)
        eel.DisplayMessage(text)
        engine.say(text)
        eel.receiverText(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[speak error]: {e}")


# ========== LISTEN ==========
def takecommand():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("listening....")
            eel.DisplayMessage("listening....")
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, 10, 6)

        print("recognizing")
        eel.DisplayMessage("recognizing....")
        query = r.recognize_google(audio, language="en-in")
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        time.sleep(2)
        return query.lower()

    except sr.WaitTimeoutError:
        print("Mic timeout — no speech detected.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except Exception as e:
        print(f"[takecommand error]: {e}")
        return ""


# ========== FILLER WORDS ==========
# Ordered longest-first. Bug #4 fix: added "my", "the", "our", "a"
FILLER_WORDS = [
    "i want you to",
    "i need you to",
    "go ahead and",
    "can you please",
    "could you please",
    "would you please",
    "can you",
    "could you",
    "would you",
    "jarvis,",
    "jarvis",
    "please",
    "hey",
    "okay",
    "ok",
    "just",
    "quickly",
    "for me",
    "i want to",
    "help me",
    # sense verbs / question prefixes
    "show me the",
    "show me",
    "tell me the",
    "tell me about",
    "tell me",
    "check the",
    "check my",
    "check",
    "get me the",
    "get me",
    "give me the",
    "give me",
    "what is the",
    "what is my",
    "what is",
    "what's the",
    "what's my",
    "how is the",
    "how is my",
    "i would like to",
    # Bug #4: possessives/articles that break app names
    " my ",
    " the ",
    " our ",
    " a ",
]


def clean_query(text):
    """Remove filler words so routing keywords are at the front."""
    t = text.lower().strip()
    for filler in FILLER_WORDS:
        t = t.replace(filler, " ")
    return " ".join(t.split())


# URL extensions — strict list (no '.in' which false-positives on 'send an email')
URL_EXTENSIONS = [
    ".com",
    ".org",
    ".net",
    ".io",
    ".gov",
    ".gg",
    ".edu",
    ".co.in",
    ".co.uk",
]


def _is_url(text):
    return any(ext in text for ext in URL_EXTENSIONS)


# ============================================================
# INTENT KEYWORD LISTS
# ============================================================

OPEN_WORDS = ["open ", "launch ", "start ", "run "]

SYSTEM_CONTROL_WORDS = [
    "shutdown",
    "shut down",
    "shut the computer down",
    "restart",
    "reboot",
    "sleep",
    "hibernate",
    "put to sleep",
    "volume up",
    "turn up volume",
    "increase volume",
    "louder",
    "volume down",
    "turn down volume",
    "decrease volume",
    "quieter",
    "mute",
    "unmute",
    "silence",
    "lock",
    "lock screen",
    "lock the computer",
]

SYSTEM_STATUS_WORDS = [
    "system status",
    "status of my machine",
    "machine status",
    "how is the system",
    "system health",
    "computer status",
    "cpu usage",
    "cpu load",
    "processor",
    "ram",
    "memory usage",
    "battery",
    "battery level",
    "battery percentage",
    "charging",
    "disk space",
    "storage",
]

BRIEFING_WORDS = [
    "morning briefing",
    "daily briefing",
    "briefing",
    "today's news",
    "news today",
    "latest news",
    "top news",
    "weather",
    "weather today",
    "today's weather",
    "weather update",
    "current weather",
    "temperature outside",
]

GMAIL_WORDS = [
    "gmail",
    "type an email",
    "compose an email",
    "send an email",
    "write an email",
    "new email",
    "compose email",
    "open my email",
]

SEARCH_WORDS = [
    "search for",
    "search about",
    "google for",
    "look up",
    "find information about",
]

YOUTUBE_WORDS = ["on youtube", "play on youtube", "youtube search"]
WHATSAPP_WORDS = [
    "send message",
    "send whatsapp",
    "phone call",
    "video call",
    "whatsapp",
    "message to",
    "text to",
]


# ========== SENIOR PROACTIVE INTENT CLASSIFIER (v2) ==========
INTENT_CLASSIFIER_PROMPT = """
## ROLE
You are the **Senior Intent Classifier & Proactive Strategist** for Jarvis, a high-performance personal AI assistant. You operate with 30 years of experience in natural language understanding and system automation.

## TASK
Analyze the user's voice query and map it to a specific system intent and its required parameters. You must detect both explicit commands and implicit needs (proactive hints).

## CONTEXT
The user interacts with Jarvis via voice. Queries can be informal, fragmented, or multi-intent. Your output is consumed by a Python backend that requires strict JSON.

## INSTRUCTIONS
1. **Analyze Core Intent**: Identify if the user wants to open an app, type text, search, control the system, or just chat.
2. **Detect Proactivity**: If the user expresses a state (e.g., "I'm tired", "PC is slow"), map it to a proactive intent (e.g., "briefing" or "status").
3. **Extract Parameters**: identify app names, contact names, messages, or specific system commands.
4. **Enforce JSON Contract**: Output MUST be a single JSON object. No prose. No markdown blocks.

## CONSTRAINTS
- Return ONLY a single JSON object.
- NO PROSE, NO EXPLANATIONS, NO MARKDOWN OUTSIDE THE JSON.
- If no specific intent matches, set intent to "chat".

## OUTPUT FORMAT
{
  "intent": "open | type | camera | whatsapp_message | whatsapp_call | search | system | status | briefing | chat",
  "parameters": {
    "app_name": "string",
    "message": "string",
    "contact": "string",
    "query": "string",
    "command": "string",
    "video": "boolean"
  },
  "confidence": 0.0-1.0,
  "proactive_suggestion": "string"
}

## EXAMPLES
Input: "type a quick hello to my boss"
Output: {"intent": "type", "parameters": {"message": "a quick hello to my boss"}, "confidence": 0.9}

Input: "My computer is acting weird today"
Output: {"intent": "status", "parameters": {}, "confidence": 0.8, "proactive_suggestion": "Let me check your system resources, sir."}

QUERY: {query}
"""


# ========== SAFE GEMINI CALL ==========
def safe_gemini_chat(raw_query):
    """Call Gemini with retry. If still fails, use local fallback."""
    try:
        return ask_gemini(raw_query)
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            print("[Gemini] Rate limit hit. Waiting 5s and retrying once...")
            time.sleep(5)
            try:
                return ask_gemini(raw_query)
            except Exception:
                pass
        print(f"[Gemini error]: {e}")
    return local_fallback()


# Exit keywords — saying any of these ends the conversation loop
EXIT_WORDS = [
    "stop",
    "bye",
    "goodbye",
    "exit",
    "go to sleep",
    "that's all",
    "thank you",
    "jarvis exit",
]


def _handle_query(q, raw):
    """Route a single cleaned query to the right handler. Returns True if handled."""

    # 1. WHATSAPP
    if any(word in q for word in WHATSAPP_WORDS):
        # Bug Fix: If user says "open whatsapp", use openCommand instead of messaging
        if any(w in q for w in ["open", "launch", "start"]):
            from engine.features import openCommand

            openCommand("whatsapp")
            return

        from engine.features import findContact, whatsApp

        contact_no, name = findContact(q)
        if contact_no != 0:
            # Determine flag: Default 'call' to voice call
            is_video = "video" in q
            is_call = "call" in q or "phone" in q

            if is_video:
                flag = "video call"
            elif is_call:
                flag = "call"
            else:
                flag = "message"

            if flag == "message":
                # Check if message is already in query (heuristic)
                msg_parts = q.split("message")
                msg = (
                    msg_parts[-1].replace("to", "").replace(name, "").strip()
                    if len(msg_parts) > 1
                    else ""
                )

                if not msg or len(msg) < 2:
                    speak(f"What message should I send to {name}?")
                    msg = takecommand()

                if msg:
                    auto_send = "type" not in q and "type" not in raw
                    whatsApp(contact_no, msg, flag, name, auto_send=auto_send)
                else:
                    speak("Message cancelled.")
            else:
                whatsApp(contact_no, "", flag, name)
        else:
            # Bug Fix: If not in DB, search in UI
            from engine.features import whatsAppSearch, remove_words

            # Extraction fix: find name after 'to' or 'call/message'
            extracted_name = ""
            if "to " in q:
                parts = q.split("to ")
                # Usually name is right after 'to'
                extracted_name = parts[-1].split()[0]  # get first word after 'to'
            else:
                extracted_name = remove_words(
                    q,
                    [
                        "ask",
                        "call",
                        "whatsapp",
                        "message",
                        "to",
                        "send",
                        "on",
                        "video",
                        "phone",
                        "hello",
                        "hi",
                        "write",
                        "an",
                    ],
                )

            extracted_name = extracted_name.strip()

            if "message" in q:
                # Ask for message if not clear
                msg_parts = q.split("message")
                msg = (
                    msg_parts[-1].replace("to", "").strip()
                    if len(msg_parts) > 1
                    else ""
                )
                if not msg or len(msg) < 2:
                    speak(f"What message should I send?")
                    msg = takecommand()

                if msg:
                    whatsAppSearch(extracted_name, "message", msg)
            elif "video" in q:
                whatsAppSearch(extracted_name, "video call")
            else:
                whatsAppSearch(extracted_name, "call")

    # 2. GMAIL / EMAIL
    elif any(word in q for word in GMAIL_WORDS):
        from engine.features import webAutomation

        webAutomation(q)

    # 3. SEARCH
    elif any(word in q for word in SEARCH_WORDS):
        from engine.features import webAutomation

        webAutomation(q)

    # 4. TYPE / KEYBOARD
    elif "type " in q or "write " in q:
        from engine.features import typeCommand

        msg = q.replace("type", "").replace("write", "").strip()
        typeCommand(msg)

    # 5. CAMERA
    elif "camera" in q or "webcam" in q:
        from engine.features import cameraCommand

        cameraCommand()

    # 6. OPEN / URL
    elif any(q.startswith(w) for w in OPEN_WORDS) or _is_url(q):
        from engine.features import openCommand

        app_name = q
        for w in OPEN_WORDS:
            if app_name.startswith(w):
                app_name = app_name[len(w) :].strip()
                break
        openCommand(app_name)

    # 5. YOUTUBE
    elif any(word in q for word in YOUTUBE_WORDS) or ("play" in q and "youtube" in q):
        from engine.features import PlayYoutube

        PlayYoutube(q)

    # 6. SYSTEM CONTROL
    elif any(word in q for word in SYSTEM_CONTROL_WORDS):
        from engine.features import systemControl

        systemControl(q)

    # 7. SYSTEM STATUS
    elif any(word in q for word in SYSTEM_STATUS_WORDS):
        from engine.features import systemInfo

        systemInfo()

    # 8. BRIEFING / NEWS / WEATHER
    elif any(word in q for word in BRIEFING_WORDS):
        from engine.features import morningBriefing

        morningBriefing()

    # 11. FALLBACK: Senior Intent Classifier
    else:
        print(f"[Gemini fallback] for: '{raw}'")
        import json

        try:
            classification_raw = safe_gemini_chat(
                INTENT_CLASSIFIER_PROMPT.format(query=raw)
            )

            # Robust JSON extraction using Regex
            match = re.search(r"\{.*\}", classification_raw, re.DOTALL)
            if not match:
                raise ValueError("No JSON found in Gemini output")

            data = json.loads(match.group())

            intent = data.get("intent")
            params = data.get("parameters", {})
            proactive_msg = data.get("proactive_suggestion")

            if proactive_msg:
                speak(proactive_msg)

            if intent == "type":
                from engine.features import typeCommand

                typeCommand(params.get("message"))
                return
            elif intent == "camera":
                from engine.features import cameraCommand

                cameraCommand()
                return
            elif intent == "open":
                from engine.features import openCommand

                openCommand(params.get("app_name"))
                return
            elif intent == "whatsapp_message":
                from engine.features import findContact, whatsApp, whatsAppSearch

                contact_no, name = findContact(params.get("contact"))
                if contact_no != 0:
                    msg = params.get("message")
                    if not msg or len(msg) < 2:
                        speak(f"What message should I send to {name} sir?")
                        msg = takecommand()

                    if msg:
                        # If user says "type", don't auto-send
                        auto_send = "type" not in raw
                        whatsApp(contact_no, msg, "message", name, auto_send=auto_send)
                    else:
                        speak("Message cancelled.")
                    return
                else:
                    # Fallback to search
                    name = params.get("contact")
                    msg = params.get("message")
                    if not msg:
                        speak(f"What message should I send to {name} sir?")
                        msg = takecommand()
                    whatsAppSearch(name, "message", msg)
                    return
            elif intent == "whatsapp_call":
                from engine.features import findContact, whatsApp, whatsAppSearch

                contact_no, name = findContact(params.get("contact"))
                if contact_no != 0:
                    # Default 'call' to voice call unless video explicitly requested
                    video = params.get("video")
                    if video is None:
                        video = "video" in raw

                    flag = "video call" if video else "call"
                    whatsApp(contact_no, "", flag, name)
                    return
                else:
                    # Fallback to search
                    name = params.get("contact")
                    video = params.get("video")
                    if video is None:
                        video = "video" in raw

                    flag = "video call" if video else "call"
                    whatsAppSearch(name, flag)
                    return
            elif intent == "search":
                from engine.features import webAutomation

                webAutomation(f"search {params.get('query')}")
                return
            elif intent == "status":
                from engine.features import systemInfo

                systemInfo()
                return
            elif intent == "briefing":
                from engine.features import morningBriefing

                morningBriefing()
                return
            elif intent == "system":
                from engine.features import systemControl

                systemControl(params.get("command"))
                return

        except Exception as e:
            print(f"[Intent Classifier Error]: {e}")

        # Final Fallback: Simple Chat
        reply = safe_gemini_chat(raw)
        print(f"Jarvis: {reply}")
        speak(reply)


# ========== COMMAND HANDLER ==========
@eel.expose
def allCommands(message=1):
    # Signal hotword process that we're busy
    if _jarvis_busy:
        _jarvis_busy.set()

    try:
        # --- TEXT INPUT (from chatbox) → single-shot, no loop ---
        if message != 1:
            eel.senderText(message)
            raw = message.lower().strip()
            q = clean_query(raw)
            print(f"Raw: '{raw}' | Cleaned: '{q}'")
            _handle_query(q, raw)
            return

        # --- VOICE INPUT → CONTINUOUS CONVERSATION LOOP ---
        silent_count = 0
        MAX_SILENT = 2  # go back to start page after 2 silences in a row

        while True:
            query = takecommand()

            if not query:
                silent_count += 1
                print(f"[silence {silent_count}/{MAX_SILENT}]")
                if silent_count >= MAX_SILENT:
                    print("[conversation ended — too many silences]")
                    break  # exit loop → go back to start page
                # Stay on listening page, try again
                eel.DisplayMessage("I didn't catch that. I'm still listening...")
                continue

            # Got a valid query — reset silence counter
            silent_count = 0
            eel.senderText(query)

            raw = query.lower().strip()
            q = clean_query(raw)
            print(f"Raw: '{raw}' | Cleaned: '{q}'")

            # Check for EXIT command
            if any(word in q for word in EXIT_WORDS):
                speak(
                    "Alright sir, going back to standby. Just say my name when you need me!"
                )
                break  # exit loop → go back to start page

            # Handle the command
            try:
                _handle_query(q, raw)
            except Exception as e:
                print(f"[command error]: {e}")
                try:
                    speak("Sorry, I ran into a problem. Go ahead, I'm still listening.")
                except Exception:
                    pass

            # Stay on listening page for next command
            eel.KeepListening()
            print("[ready for next command...]")

    except Exception as e:
        print(f"[allCommands fatal error]: {e}")

    finally:
        # Always clear the busy flag so hotword resumes
        if _jarvis_busy:
            _jarvis_busy.clear()
        # Return to start page (blue sphere)
        try:
            eel.ShowHood()
        except Exception as e:
            print(f"[UI reset error]: {e}")
