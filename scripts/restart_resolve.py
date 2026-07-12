#!/usr/bin/env python3
"""Graceful Resolve restart (doctrine: save -> quit -> WAIT -> relaunch -> wait).

Prototype of the Studio Daemon's lifecycle verb. Never pkill.
Usage: .venv/bin/python scripts/restart_resolve.py [--nogui]
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

APP = "/Applications/DaVinci Resolve/DaVinci Resolve.app"
BIN = f"{APP}/Contents/MacOS/Resolve"


def is_running():
    return subprocess.run(["pgrep", "-x", "Resolve"], capture_output=True).returncode == 0


def main():
    nogui = "--nogui" in sys.argv

    if is_running():
        try:
            from studio.resolve import connect
            connect().GetProjectManager().SaveProject()
            print("saved current project")
        except Exception as e:
            print(f"save skipped: {e}")
        subprocess.run(["osascript", "-e", 'quit app "DaVinci Resolve"'],
                       capture_output=True)
        t0 = time.time()
        while is_running():
            if time.time() - t0 > 60:
                print("FAIL: Resolve did not exit within 60s (dialog blocking?)")
                return 1
            time.sleep(2)
        print(f"exited after {time.time()-t0:.0f}s")
        time.sleep(5)  # let locks/shared state settle — libggml lesson

    if nogui:
        subprocess.Popen([BIN, "-nogui"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    else:
        subprocess.run(["open", "-a", APP], check=True)

    from studio.resolve import connect, ResolveUnavailable
    t0 = time.time()
    while time.time() - t0 < 120:
        try:
            app = connect()
            print(f"API up after {time.time()-t0:.0f}s: {app.GetVersionString()}")
            return 0
        except ResolveUnavailable:
            time.sleep(3)
    print("FAIL: API never came up within 120s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
