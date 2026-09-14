
import os
import sys
import time
import socket
import threading
import traceback
import tempfile

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8000

def log_path():
    return os.path.join(tempfile.gettempdir(), "GEORUSH-SEO-startup-error.txt")

def write_error(exc):
    try:
        with open(log_path(), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
            f.write("\nException: " + repr(exc) + "\n")
    except Exception:
        pass

def wait_for_port(timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.3):
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
    except Exception as exc:
        write_error(exc)

def main():
    thread = threading.Thread(target=start_api, daemon=True)
    thread.start()

    if not wait_for_port():
        raise RuntimeError(
            "GEORUSH API could not start.\n\n"
            "Startup details: " + log_path()
        )

    webview.create_window(
        "GEORUSH SEO",
        f"http://{HOST}:{PORT}/",
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#0b1118",
        text_select=True,
    )
    webview.start()

if __name__ == "__main__":
    main()
