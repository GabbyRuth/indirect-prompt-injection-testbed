import os
from pathlib import Path

from ..http_service import start_static_server


CONTAINER_NAME = os.getenv("CALENDAR_CONTAINER_NAME", "indirect-prompt-injection-calendar")
HOSTNAME = "fake-calendar"
PORT = int(os.getenv("CALENDAR_PORT", "8090"))


def start_calendar_server(asset_dir=None):
    root = asset_dir or Path(__file__).resolve().parents[4] / "tests" / "payloads" / "calendar_payload" / "injected"
    Path(root).mkdir(parents=True, exist_ok=True)
    return start_static_server(CONTAINER_NAME, str(root), HOSTNAME, PORT, PORT)


def runner_environment():
    return {"CALENDAR_URL": f"http://{HOSTNAME}:{PORT}"}