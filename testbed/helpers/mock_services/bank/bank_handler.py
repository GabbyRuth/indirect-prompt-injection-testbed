import os
from pathlib import Path

from ..http_service import start_script_server


CONTAINER_NAME = os.getenv("BANK_CONTAINER_NAME", "indirect-prompt-injection-bank")
HOSTNAME = "fake-bank"
PORT = int(os.getenv("BANK_PORT", "8081"))


def start_bank_server():
    return start_script_server(
        CONTAINER_NAME, str(Path(__file__).with_name("server.py")),
        HOSTNAME, PORT, PORT
    )


def runner_environment():
    return {"BANK_API_URL": f"http://{HOSTNAME}:{PORT}"}