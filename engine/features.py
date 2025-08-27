from playsound import playsound
import eel


# playing assistant sound function

@eel.expose
def playAssistantSound():
    music_dir=r"www\assets\vendore\texllate\audio\sounds.mpeg"
    playsound(music_dir) 