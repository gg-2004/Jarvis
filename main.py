import os
import eel
import threading
import time
import subprocess

from engine.features import *
from engine.command import allCommands, set_busy_event


def clear_port(port):
    """Force kill any process using the specified port on Windows."""
    try:
        # Find PIDs using the port
        output = subprocess.check_output(
            f"netstat -ano | findstr :{port}", shell=True
        ).decode()
        for line in output.strip().split("\n"):
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                print(f"[main] Killing existing process {pid} on port {port}...")
                os.system(f"taskkill /F /PID {pid} /T")
                time.sleep(1)
    except Exception:
        pass


def hotword_trigger_watcher(event):
    """Wait for hotword_triggered event and call allCommands."""
    while True:
        if event.is_set():
            print("[main] Hotword trigger event caught!")
            event.clear()
            # 1. Update UI to SiriWave
            try:
                eel.KeepListening()
            except Exception:
                pass
            # 2. Trigger conversation loop
            # Run in separate thread so we don't block the watcher
            threading.Thread(target=allCommands, args=(1,), daemon=True).start()
        time.sleep(0.1)


def start(jarvis_busy=None, hotword_triggered=None):
    # Wire the busy event into command module
    if jarvis_busy:
        set_busy_event(jarvis_busy)

    # Start the hotword watcher thread
    if hotword_triggered:
        threading.Thread(
            target=hotword_trigger_watcher, args=(hotword_triggered,), daemon=True
        ).start()

    # Ensure port 5500 is free before starting
    clear_port(5500)

    eel.init("www")

    playAssistantSound()

    os.system('start msedge.exe --app="http://127.0.0.1:5500/index.html"')

    def on_close(page, sockets):
        if not sockets:
            print("[eel] Browser disconnected — reopening Edge window...")
            os.system('start msedge.exe --app="http://127.0.0.1:5500/index.html"')

    eel.start(
        "index.html",
        mode=None,
        host="localhost",
        port=5500,
        block=True,
        close_callback=on_close,
    )
