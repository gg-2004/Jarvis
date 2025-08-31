import os
import re
import sqlite3
import struct
import time
import webbrowser
from playsound import playsound
import eel
import pvporcupine
import pyaudio
from engine.command import speak
from engine.config import ASSISTANT_NAME
import pywhatkit as kit

from engine.helper import extract_yt_term


con = sqlite3.connect("jarvis.db")
cursor = con.cursor()



# playing assistant sound function

@eel.expose
def playAssistantSound():
    music_dir=r"www\assets\vendore\texllate\audio\sounds.mpeg"
    playsound(music_dir) 


def openCommand(query):
    query =  query.replace(ASSISTANT_NAME, "")
    query = query.replace("open","")
    query.lower()

    app_name = query.strip()

    if app_name != "":

        try:
            cursor.execute(
                'SELECT path FROM sys_command WHERE name IN (?)',(app_name,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening "+query)
                os.startfile(results[0][0])

            elif len(results) == 0:
                cursor.execute(
                    'SELECT url FROM web_command WHERE name IN (?)',(app_name,))
                results = cursor.fetchall()
                
                if len(results)!= 0:
                    speak("Opening "+query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening "+query)
                    try:
                        os.system('start '+query)
                    except:
                        speak("not found")
        except:
            speak ("some thing went wrong")                 


def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:   # only if regex found something
        speak("Playing " + search_term + " on Youtube")
        kit.playonyt(search_term)
    else:
        speak("I could not understand what to play on Youtube")

def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
        #pre trained keywords
        porcupine=pvporcupine.create(keywords=["jarvis","alexa"])
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)

        #loop for streaming
        while True:
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from ("h"*porcupine.frame_length,keyword)
   
            #processing keyword detected for mic
            keyword_index=porcupine.process(keyword)

            #checking first keyword detected for not
            if keyword_index>=0:
               print("hotword detected")

               #pressing shortcut key win+j
               import pyautogui as autogui
               autogui.keyDown("win")
               autogui.press("j")
               time.sleep(2)
               autogui.keyUp("win ")
                  


    except Exception as e:
        print("Error:", e)
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()