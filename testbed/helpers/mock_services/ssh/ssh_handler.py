import os
from pathlib import Path

from ..http_service import start_script_server


CONTAINER_NAME = os.getenv("SSH_CONTAINER_NAME", "indirect-prompt-injection-ssh")
HOSTNAME = "fake-ssh"
PORT = int(os.getenv("SSH_PORT", "2222"))


def start_ssh_server():
    return start_script_server(
        CONTAINER_NAME, str(Path(__file__).with_name("server.py")),
        HOSTNAME, PORT, PORT
    )


def runner_environment():
    return {"SSH_HOST": HOSTNAME, "SSH_PORT": str(PORT)}
