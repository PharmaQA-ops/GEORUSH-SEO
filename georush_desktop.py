"""GEORUSH one-click Windows desktop launcher.

Starts/uses Ollama silently, ensures the configured local model exists,
starts the GEORUSH FastAPI backend, and opens the desktop UI.
"""
import os
import sys
import time
import socket
import threading
import traceback
import tempfile
import shutil
import subprocess
from pathlib import Path

import httpx
import uvicorn
import webview

HOST = "127.0.0.1"
PORT = int(os.getenv("GEORUSH_PORT", "8000"))
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
STARTUP_TIMEOUT = int(os.getenv("GEORUSH_STARTUP_TIMEOUT", "120"))

ollama_process = None
started_ollama = False


def log_path():
    return os.path.join(tempfile.gettempdir(), "GEORUSH-SEO-startup-error.txt")


def write_log(message=""):
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
            if message == "":
                f.write(traceback.format_exc())
    except Exception:
        pass


def windows_hidden_kwargs():
    if os.name != "nt":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def find_ollama():
    candidates = [
        shutil.which("ollama"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Ollama", "ollama.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def ollama_online():
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.5)
        return r.status_code == 200
    except Exception:
        return False


def model_available():
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [str(x.get("name", "")) for x in r.json().get("models", [])]
        return OLLAMA_MODEL in models
    except Exception:
        return False


def start_ollama():
    global ollama_process, started_ollama
    if ollama_online():
        return True

    exe = find_ollama()
    if not exe:
        write_log("Ollama executable was not found. Install Ollama from https://ollama.com/download")
        return False

    try:
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"{OLLAMA_HOST}:{OLLAMA_PORT}"
        ollama_process = subprocess.Popen(
            [exe, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            **windows_hidden_kwargs(),
        )
        started_ollama = True
    except Exception as exc:
        write_log(f"Could not start Ollama: {exc!r}")
        return False

    end = time.time() + STARTUP_TIMEOUT
    while time.time() < end:
        if ollama_online():
            return True
        time.sleep(0.5)
    write_log("Ollama did not become ready within the startup timeout.")
    return False


def ensure_model():
    if model_available():
        return True
    exe = find_ollama()
    if not exe:
        return False
    try:
        # First run may need to download the model. Keep it hidden and wait.
        result = subprocess.run(
            [exe, "pull", OLLAMA_MODEL],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1800,
            **windows_hidden_kwargs(),
        )
        return result.returncode == 0 and model_available()
    except Exception as exc:
        write_log(f"Could not pull Ollama model {OLLAMA_MODEL}: {exc!r}")
        return False


def wait_for_port(timeout=STARTUP_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.4):
                return True
        except OSError:
            time.sleep(0.25)
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
        write_log(f"GEORUSH API startup failed: {exc!r}")


def cleanup():
    global ollama_process
    # Only stop Ollama if this GEORUSH launcher started it.
    if started_ollama and ollama_process is not None:
        try:
            ollama_process.terminate()
        except Exception:
            pass


def startup():
    if not start_ollama():
        raise RuntimeError(
            "Ollama could not be started.\n\n"
            f"Make sure Ollama is installed. Startup log: {log_path()}"
        )

    if not ensure_model():
        raise RuntimeError(
            f"Ollama is running, but model '{OLLAMA_MODEL}' is unavailable.\n\n"
            f"Startup log: {log_path()}"
        )

    thread = threading.Thread(target=start_api, daemon=True)
    thread.start()
    if not wait_for_port():
        raise RuntimeError(
            "GEORUSH API could not start.\n\n"
            f"Startup log: {log_path()}"
        )


def main():
    try:
        startup()
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
    except Exception as exc:
        write_log(f"Launcher error: {exc!r}")
        # If running from a terminal, make the error visible; packaged EXE users
        # can inspect the temp log instead.
        if sys.stdout:
            try:
                print(str(exc))
            except Exception:
                pass
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
