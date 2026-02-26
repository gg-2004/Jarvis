# to run jarvis
import multiprocessing
import time


def startJarvis(jarvis_busy, hotword_triggered):
    # code for process 1 (main app + eel server)
    print("Process 1 is running.")
    from main import start

    start(jarvis_busy, hotword_triggered)


def listenHotword(jarvis_busy, hotword_triggered):
    # code for process 2 (hotword detection)
    print("Process 2 is running.")
    from engine.features import hotword

    hotword(jarvis_busy, hotword_triggered)


# start both processes
if __name__ == "__main__":
    # Shared flag: set() while Jarvis is actively listening/speaking
    jarvis_busy = multiprocessing.Event()
    # Shared flag: set() when hotword is detected
    hotword_triggered = multiprocessing.Event()

    p1 = multiprocessing.Process(
        target=startJarvis, args=(jarvis_busy, hotword_triggered)
    )
    p2 = multiprocessing.Process(
        target=listenHotword, args=(jarvis_busy, hotword_triggered)
    )

    p1.start()
    p2.start()

    # Supervisor loop
    while True:
        if not p1.is_alive():
            print("[run.py] Process 1 (Jarvis) died — restarting...")
            p1 = multiprocessing.Process(
                target=startJarvis, args=(jarvis_busy, hotword_triggered)
            )
            p1.start()

        if not p2.is_alive():
            print("[run.py] Process 2 (Hotword) died — restarting...")
            p2 = multiprocessing.Process(
                target=listenHotword, args=(jarvis_busy, hotword_triggered)
            )
            p2.start()

        time.sleep(5)  # check every 5 seconds (give OS time to release sockets)
