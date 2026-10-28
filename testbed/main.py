import docker_handler as docker_handler
import os
from pathlib import Path

# this will dynamically inject our attack randomly into the payload
import helpers.prompt_injector as prompt_injector

# this handles the test cases that include extra needs such as hosting a webserver, spoofing bank apis, calendar servers, email servers, putting files on the system
import helpers.outcome_handler as outcome_handler

agent_names = [
    "claude",
    "custom",
    "open_claw"
]

payloads_root = Path("tests/payloads")
attacks_root = Path("tests/attacks")


def read_text(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return f.read().strip()


def iter_files(path: Path):
    return sorted([p for p in path.iterdir() if p.is_file()])


if not payloads_root.exists() or not attacks_root.exists():
    raise FileNotFoundError("Expected tests/payloads and tests/attacks directories.")

attack_files = sorted(attacks_root.glob("*.txt"))
if not attack_files:
    raise FileNotFoundError("No attack files found in tests/attacks.")

for payload_dir in sorted(payloads_root.iterdir()):
    if not payload_dir.is_dir():
        continue

    prompt_file = payload_dir / "prompt.txt"
    clean_dir = payload_dir / "clean"
    injected_dir = payload_dir / "injected"

    if not prompt_file.exists() or not clean_dir.exists():
        print(f"Skipping payload '{payload_dir.name}' (missing prompt.txt or clean/).")
        continue

    injected_dir.mkdir(parents=True, exist_ok=True)
    clean_assets = iter_files(clean_dir)
    if not clean_assets:
        print(f"Skipping payload '{payload_dir.name}' (no files in clean/).")
        continue

    prompt = read_text(prompt_file)

    for attack_file in attack_files:
        attack_name = attack_file.stem
        attack = read_text(attack_file)

        for agent in agent_names:
            for clean_asset in clean_assets:
                injected_asset = prompt_injector.inject_attack(
                    str(clean_asset),
                    attack,
                    injected_assets_dir=str(injected_dir),
                    attack_label=attack_name
                )

                if not injected_asset:
                    print(
                        f"Failed to inject attack '{attack_name}' into '{clean_asset.name}' "
                        f"for payload '{payload_dir.name}' and agent '{agent}'."
                    )
                    continue

                if os.path.isfile(injected_asset):
                    print(
                        f"Running payload '{payload_dir.name}', attack '{attack_name}', "
                        f"agent '{agent}', asset '{os.path.basename(injected_asset)}'."
                    )

                    if Path(injected_asset).suffix.lower() == ".pdf":
                        docker_handler.run_test(agent, prompt, asset=injected_asset)
                    else:
                        docker_handler.run_test(agent, prompt)
                