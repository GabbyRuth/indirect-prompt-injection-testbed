import atexit
import os
import socket
import time
from pathlib import Path
from typing import Optional

import docker
from docker.errors import APIError, NotFound


NETWORK_NAME = os.getenv(
    "MAILPIT_NETWORK_NAME",
    "indirect-prompt-injection-network",
)
PYTHON_IMAGE = os.getenv("MOCK_SERVICE_IMAGE", "python:3.13-slim")

_client: Optional[docker.DockerClient] = None
_network: Optional[docker.models.networks.Network] = None
_owned_containers: list[docker.models.containers.Container] = []
_owned_network = False


def _wait_for_port(host_port: int) -> None:
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", host_port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Mock service port {host_port} did not become ready")


def _client_or_default(client=None):
    global _client
    _client = client or _client or docker.from_env()
    return _client


def network(client=None):
    global _network, _owned_network
    client = _client_or_default(client)
    if _network is not None:
        return _network
    try:
        _network = client.networks.get(NETWORK_NAME)
    except NotFound:
        _network = client.networks.create(
            NETWORK_NAME, driver="bridge", labels={"testbed.service": "network"}
        )
        _owned_network = True
    return _network


def start_static_server(
    name: str,
    root: str,
    hostname: str,
    container_port: int,
    host_port: int,
    client=None,
):
    client = _client_or_default(client)
    service_network = network(client)
    root_path = str(Path(root).resolve())
    try:
        container = client.containers.get(name)
        container.reload()
        if container.status != "running":
            container.start()
    except NotFound:
        container = client.containers.run(
            PYTHON_IMAGE,
            name=name,
            hostname=hostname,
            command=["python", "-m", "http.server", str(container_port), "--directory", "/srv"],
            detach=True,
            network=service_network.name,
            volumes={root_path: {"bind": "/srv", "mode": "ro"}},
            ports={f"{container_port}/tcp": host_port},
            labels={"testbed.service": name},
        )
        _owned_containers.append(container)
    _wait_for_port(host_port)
    return container


def start_script_server(
    name: str,
    script: str,
    hostname: str,
    container_port: int,
    host_port: int,
    client=None,
):
    client = _client_or_default(client)
    service_network = network(client)
    script_path = str(Path(script).resolve())
    try:
        container = client.containers.get(name)
        container.reload()
        if container.status != "running":
            container.start()
    except NotFound:
        container = client.containers.run(
            PYTHON_IMAGE,
            name=name,
            hostname=hostname,
            command=["python", f"/srv/{Path(script).name}"],
            detach=True,
            network=service_network.name,
            volumes={script_path: {"bind": f"/srv/{Path(script).name}", "mode": "ro"}},
            ports={f"{container_port}/tcp": host_port},
            labels={"testbed.service": name},
        )
        _owned_containers.append(container)
    _wait_for_port(host_port)
    return container


def stop_services():
    global _network
    for container in _owned_containers:
        try:
            container.remove(force=True)
        except (APIError, NotFound):
            pass
    _owned_containers.clear()
    if _network is not None and _owned_network:
        try:
            _network.remove()
        except (APIError, NotFound):
            pass
    _network = None


atexit.register(stop_services)
