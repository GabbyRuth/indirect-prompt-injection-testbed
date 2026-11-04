import os
import docker
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = docker.from_env()
RUNNER_NETWORK_NAME = os.getenv(
    "MAILPIT_NETWORK_NAME",
    "indirect-prompt-injection-network",
)

def run_test(
    agent: str,
    prompt: str,
    asset: Optional[str] = None,
    original_filename: Optional[str] = None
):
    image_tag = "prompt-injection-runner:latest"

    # Always rebuild so local code edits are reflected in test containers.
    print(f"Building image '{image_tag}' from Docker/Dockerfile...")
    client.images.build(
        path=os.path.dirname(__file__),
        dockerfile="Docker/Dockerfile",
        tag=image_tag,
        rm=True
    )

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
            else:
                from helpers.mock_services.email.email_handler import (
                    runner_environment,
                )

            environment.update(runner_environment())

        # Spin up isolated container with targeted env vars and volume
        container = client.containers.run(
            image=image_tag,
            environment=environment,
            volumes=volumes if volumes else None,
            network=network,
            detach=True
        )

        # Wait for completion to capture full execution logs
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
