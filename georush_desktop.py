
import os
import sys
import time
import socket
import subprocess
import threading
import webview

HOST = "127.0.0.1"
PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))

api_process = None

def port_open(host, port):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()

def start_api():
    global api_process
    if port_open(HOST, PORT):
        return

    python = sys.executable
    main_py = os.path.join(ROOT, "main.py")

    api_process = subprocess.Popen(
        [python, "-m", "uvicorn", "main:app",
         "--host", HOST, "--port", str(PORT)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )

def wait_for_api():
    for _ in range(50):
        if port_open(HOST, PORT):
            return True
        time.sleep(0.2)
    return False

def on_closed():
    global api_process
    if api_process and api_process.poll() is None:
        try:
            api_process.terminate()
        except Exception:
            pass

def main():
    threading.Thread(target=start_api, daemon=True).start()

    if not wait_for_api():
        # The page can still load and explain that the API is unavailable.
        pass

    webview.create_window(
        "GEORUSH SEO",
        f"http://{HOST}:{PORT}",
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#0b1118",
        text_select=True
    )
    webview.start(debug=False)
    on_closed()

if __name__ == "__main__":
    main()
