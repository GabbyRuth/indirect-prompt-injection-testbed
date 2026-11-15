import os
from pathlib import Path

from ..http_service import start_static_server


CONTAINER_NAME = os.getenv("WEBSITE_CONTAINER_NAME", "indirect-prompt-injection-website")
HOSTNAME = "fake-website"
PORT = int(os.getenv("WEBSITE_PORT", "8091"))


def start_website_server(asset_dir=None):
    root = asset_dir or Path(__file__).resolve().parents[4] / "tests" / "payloads" / "html_payload" / "injected"
    Path(root).mkdir(parents=True, exist_ok=True)
    return start_static_server(CONTAINER_NAME, str(root), HOSTNAME, PORT, PORT)


def runner_environment():
    return {"WEBSITE_URL": f"http://{HOSTNAME}:{PORT}"}