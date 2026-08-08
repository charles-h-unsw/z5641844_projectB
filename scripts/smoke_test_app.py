"""Headless local health check for the root Streamlit app."""
from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 8765
HEALTH_URL = f"http://{HOST}:{PORT}/_stcore/health"


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def main() -> None:
    if _port_open(HOST, PORT):
        raise SystemExit(f"test port {PORT} is already in use")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--browser.gatherUsageStats=false",
    ]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 45.0
        last_error: Exception | None = None
        while time.time() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=5)
                raise RuntimeError(
                    f"Streamlit exited early with code {process.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                )
            try:
                with urllib.request.urlopen(HEALTH_URL, timeout=2) as response:
                    body = response.read().decode("utf-8", errors="replace").strip()
                    if response.status == 200 and body.lower() == "ok":
                        print(f"streamlit_health=ok url={HEALTH_URL}")
                        return
            except Exception as exc:  # server may still be starting
                last_error = exc
            time.sleep(0.5)
        raise RuntimeError(f"Streamlit health endpoint did not become ready: {last_error}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stdout, stderr = process.communicate()
        if "Traceback" in stderr or "Uncaught app exception" in stderr:
            raise RuntimeError(f"Streamlit stderr contained an app exception:\n{stderr}")


if __name__ == "__main__":
    main()
