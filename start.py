#!/usr/bin/env python3
"""
start.py - Launch script for Cleanbox.
Checks dependencies, starts the FastAPI server, and opens the app in your default browser.
"""

import sys
import os
import subprocess
import webbrowser
import time

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Determine python path (prefer local venv if available)
    venv_py = os.path.join(script_dir, "venv", "bin", "python")
    py_exec = venv_py if os.path.exists(venv_py) else sys.executable

    port = int(os.environ.get("PORT", 8000))
    url = f"http://localhost:{port}"

    print("=" * 60)
    print(" 📧  CLEANBOX (Gmail & Hotmail)")
    print("=" * 60)
    print(f" Starting web app on {url} ...")
    print(" Safe marketing detection active (purchases & bookings safeguarded)")
    print(" Largest emails flagged by size (> 1MB, > 5MB, > 10MB)")
    print(" Press Ctrl+C to stop the server.")
    print("=" * 60)

    # Automatically open browser in 1.2 seconds
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch uvicorn
    try:
        subprocess.run([
            py_exec, "-m", "uvicorn", "app:app",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped. Bye!")

if __name__ == "__main__":
    main()
