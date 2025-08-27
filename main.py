import os
import eel

from engine.features import *


eel.init("www")    

playAssistantSound()

os.system('start msedge.exe --app="http://127.0.0.1:5500/www/index.html"')

eel.start('index.html', mode= None, host='localhost',block=True)
