import docker_handler as docker_handler
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent.defenses import get_defense_combinations

# this will dynamically inject our attack randomly into the payload
import helpers.prompt_injector as prompt_injector

# this handles the test cases that include extra needs such as hosting a webserver, spoofing bank apis, calendar servers, email servers, putting files on the system
import helpers.mock_services.mock_service_factory as mock_service_factory

# agent_names = [
#    "claude",
#    "custom",
#    "open_claw"
#]

def load_assets(payload_dir, injected_asset):
    if payload_dir.name == "email_payload":
        mock_service_factory.load_email(injected_asset)

agent_names = ["custom"]

# uncomment for baseline defense (no defenses applied)
# defenses = ["baseline"]

# uncomment for all combinations of defenses
defenses = [
    "system_prompt",
    "allowlist",
    "provenance",
    "sensitive_blocking",
    "require_approval"
]

# used for testing
# defenses = ["system_prompt", "provenance"]
# defenses = ["baseline"]

defense_combinations = get_defense_combinations(defenses)
MAX_WORKERS = max(1, int(os.getenv("TESTBED_MAX_WORKERS", "2")))

project_root = Path(__file__).resolve().parent.parent
payloads_root = project_root / "tests" / "payloads"
attacks_root = project_root / "tests" / "attacks"


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

docker_handler.build_runner_image()

for service_name in ("email_payload", "calendar_payload", "html_payload"):
    mock_service_factory.create_service(service_name)

for attack_file in attack_files:
    mock_service_factory.create_service(attack_file.stem)

jobs = []
for payload_dir in sorted(payloads_root.iterdir()):
    if not payload_dir.is_dir():
        continue

    # spin up the mock services for this payload if needed
    service_name = payload_dir.name
    mock_service_factory.create_service(service_name)


    prompt_file = payload_dir / "prompt.txt"
    clean_dir = payload_dir / "clean"
    injected_dir = payload_dir / "injected"

    if not prompt_file.exists() or not clean_dir.exists():
        print(f"Skipping payload '{payload_dir.name}' (missing prompt.txt or clean/).")
        continue

    injected_dir.mkdir(parents=True, exist_ok=True)
    mock_service_factory.create_service(payload_dir.name, str(injected_dir))
    clean_assets = iter_files(clean_dir)
    if not clean_assets:
        print(f"Skipping payload '{payload_dir.name}' (no files in clean/).")
        continue

    prompt = read_text(prompt_file)

    for attack_file in attack_files:
        attack_name = attack_file.stem
        attack = read_text(attack_file)

        for agent in agent_names:
            for defense in defense_combinations:
                for clean_asset in clean_assets:
                    injected_asset = prompt_injector.inject_attack(
                        str(clean_asset),
                        attack,
                        injected_assets_dir=str(injected_dir),
                        attack_label=attack_name,
                    )

                    if not injected_asset or not os.path.isfile(injected_asset):
                        print(
                            f"Failed to inject attack '{attack_name}' into "
                            f"'{clean_asset.name}' for payload '{payload_dir.name}'."
                        )
                        continue

                    full_prompt = f"{prompt}\n\nThe document is named: {clean_asset.name}"
                    load_assets(payload_dir, injected_asset)
                    jobs.append(
                        (
                            payload_dir.name,
                            attack_name,
                            agent,
                            defense,
                            clean_asset.name,
                            injected_asset,
                            full_prompt,
                        )
                    )


def run_job(job):
    payload_name, attack_name, agent, defense, asset_name, asset, prompt = job
    print(
        f"Running payload '{payload_name}', attack '{attack_name}', "
        f"agent '{agent}', defense '{defense}', asset '{asset_name}'."
    )
    docker_handler.run_test(
        agent,
        prompt,
        asset=asset,
        original_filename=asset_name,
        defense=defense,
        payload_name=payload_name,
        attack_name=attack_name,
    )


print(f"Running {len(jobs)} jobs with {MAX_WORKERS} workers.")
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(run_job, job) for job in jobs]
    for future in as_completed(futures):
        future.result()
                    
                
