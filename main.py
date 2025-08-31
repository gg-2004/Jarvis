import os
import eel


from engine.features import * 
from engine.command import *


def start():
    
    eel.init("www")    

    playAssistantSound()

    os.system('start msedge.exe --app="http://127.0.0.1:5500/index.html"')

    eel.start('index.html', mode= None, host='localhost', port=5500, block=True)
  