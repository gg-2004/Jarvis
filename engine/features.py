import os
import re
from playsound import playsound
import eel
from engine.command import speak
from engine.config import ASSISTANT_NAME
import pywhatkit as kit


# playing assistant sound function

@eel.expose
def playAssistantSound():
    music_dir=r"www\assets\vendore\texllate\audio\sounds.mpeg"
    playsound(music_dir) 


def openCommand(query):
    query =  query.replace(ASSISTANT_NAME, "")
    query = query.replace("open","")
    query.lower()

    if query!="":
        speak("Opening "+query)
        os.system('start '+query)
    else:
        speak("not found")    


def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:   # only if regex found something
        speak("Playing " + search_term + " on Youtube")
        kit.playonyt(search_term)
    else:
        speak("I could not understand what to play on Youtube")

    

def  extract_yt_term(command):
    pattern = r'play\s+(.*?)\s+on\s+youtube'
    match = re.search(pattern,command,re.IGNORECASE)
    return match.group(1) if match else None   