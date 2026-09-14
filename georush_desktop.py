
import os
import sys
import time
import socket
import threading
import traceback

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8000

def wait_for_port(host, port, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.2)
    return False

def start_api():
    try:
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
    except Exception:
        log = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "georush-startup-error.txt")
        try:
            with open(log, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass

def main():
    thread = threading.Thread(target=start_api, daemon=True)
    thread.start()

    if not wait_for_port(HOST, PORT):
        log = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "georush-startup-error.txt")
        message = "GEORUSH API could not start."
        if os.path.exists(log):
            message += "\n\nSee georush-startup-error.txt for details."
        raise RuntimeError(message)

    webview.create_window(
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
