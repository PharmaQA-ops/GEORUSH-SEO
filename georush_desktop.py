
import os
import sys
import threading
import time
import socket

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8000

def resource_root():
    # PyInstaller --onefile extracts bundled resources here.
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def wait_for_port(host, port, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.15)
    return False

def start_api():
    # main.py is bundled as a Python module by PyInstaller.
    import main
    config = uvicorn.Config(
        main.app,
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server.run()

def main():
    threading.Thread(target=start_api, daemon=True).start()

    if not wait_for_port(HOST, PORT):
        raise RuntimeError("GEORUSH API could not start.")

    window = webview.create_window(
        "GEORUSH SEO",
        f"http://{HOST}:{PORT}/",
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#0b1118",
    )
    webview.start()

if __name__ == "__main__":
    main()
