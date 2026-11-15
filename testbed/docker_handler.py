import os
import docker
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = docker.from_env()
RUNNER_NETWORK_NAME = os.getenv(
    "MAILPIT_NETWORK_NAME",
    "indirect-prompt-injection-network",
)
IMAGE_TAG = "prompt-injection-runner:latest"


def build_runner_image() -> None:
    """Build the runner image once before parallel test execution."""
    print(f"Building image '{IMAGE_TAG}' from Docker/Dockerfile...")
    client.images.build(
        path=os.path.dirname(__file__),
        dockerfile="Docker/Dockerfile",
        tag=IMAGE_TAG,
        rm=True,
    )


def run_test(
    agent: str,
    prompt: str,
    asset: Optional[str] = None,
    original_filename: Optional[str] = None,
    defense: tuple[str, ...] | str = "baseline"
):
    #  Resolve absolute path for isolated asset mounting
    volumes = {}
    if asset:
        abs_asset_path = os.path.abspath(asset)
        asset_name = original_filename or os.path.basename(abs_asset_path)
        asset_name = Path(asset_name).name
        volumes[abs_asset_path] = {
            "bind": f"/app/assets/{asset_name}",
            "mode": "ro"
        }

    project_root = Path(__file__).resolve().parent.parent
    fixture_paths = {
        project_root / "tests" / "payloads" / "agent_payload" / "clean" / "agents.md": "agents.md",
        project_root / "tests" / "fixtures" / "password.txt": "password.txt",
    }
    for fixture_path, filename in fixture_paths.items():
        if fixture_path.is_file():
            bind_path = f"/app/assets/{filename}"
            if not any(volume["bind"] == bind_path for volume in volumes.values()):
                volumes[str(fixture_path)] = {
                    "bind": bind_path,
                    "mode": "ro",
                }

    # Mount logs directory
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    volumes[str(logs_dir)] = {
        "bind": "/app/logs",
        "mode": "rw"
    }


    container = None
    try:
        environment = {
            "AGENT_NAME": agent,
            "PROMPT": prompt,
            "DEFENSE": json.dumps(
                [defense] if isinstance(defense, str) else list(defense)
            ),
            "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
            "AGENT_LOG_DIR": "/app/logs",
        }

        try:
            client.networks.get(RUNNER_NETWORK_NAME)
            network = RUNNER_NETWORK_NAME
        except docker.errors.NotFound:
            network = None

        if network:
            if __package__:
                from testbed.helpers.mock_services.email.email_handler import (
                    runner_environment,
                )
                from testbed.helpers.mock_services.calendar.calendar_handler import (
                    runner_environment as calendar_environment,
                )
                from testbed.helpers.mock_services.website.website_handler import (
                    runner_environment as website_environment,
                )
                from testbed.helpers.mock_services.bank.bank_handler import (
                    runner_environment as bank_environment,
                )
                from testbed.helpers.mock_services.ssh.ssh_handler import (
                    runner_environment as ssh_environment,
                )
            else:
                from helpers.mock_services.email.email_handler import (
                    runner_environment,
                )
                from helpers.mock_services.calendar.calendar_handler import (
                    runner_environment as calendar_environment,
                )
                from helpers.mock_services.website.website_handler import (
                    runner_environment as website_environment,
                )
                from helpers.mock_services.bank.bank_handler import (
                    runner_environment as bank_environment,
                )
                from helpers.mock_services.ssh.ssh_handler import (
                    runner_environment as ssh_environment,
                )

            environment.update(runner_environment())
            environment.update(calendar_environment())
            environment.update(website_environment())
            environment.update(bank_environment())
            environment.update(ssh_environment())

        # Spin up isolated container with targeted env vars and volume
        container = client.containers.run(
            image=IMAGE_TAG,
            environment=environment,
            volumes=volumes if volumes else None,
            network=network,
            detach=True
        )

        result = container.wait()
        exit_code = result.get("StatusCode", -1)

        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        print(f"=== Execution Completed [Agent: {agent} | Status Code: {exit_code}] ===")
        print(logs)

    except docker.errors.DockerException as e:
        print(f"Docker API Error: {e}")
    finally:
        # Clean up container safely
        if container:
            try:
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
