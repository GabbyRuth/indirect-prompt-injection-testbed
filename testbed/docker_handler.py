import os
import docker
from typing import Optional

client = docker.from_env()

def run_test(agent: str, prompt: str, asset: Optional[str] = None):
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
        asset_name = os.path.basename(abs_asset_path)
        volumes[abs_asset_path] = {
            "bind": f"/app/assets/{asset_name}",
            "mode": "ro"
        }


    

    container = None
    try:
        # Spin up isolated container with targeted env vars and volume
        container = client.containers.run(
            image=image_tag,
            environment={
                "AGENT_NAME": agent,
                "PROMPT": prompt,
                "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
            },
            volumes=volumes if volumes else None,
            detach=True
        )

        # Wait for completion to capture full execution logs
        result = container.wait()
        exit_code = result.get("StatusCode", -1)

        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        print(f"=== Execution Completed [Agent: {agent} | Status Code: {exit_code}] ===")
        print(logs)

    except docker.errors.PyDockerError as e:
        print(f"Docker API Error: {e}")
    finally:
        # Clean up container safely
        if container:
            try:
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
