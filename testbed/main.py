import docker_handler
import os

# this will dynamically inject our attack randomly into the payload
import prompt_injector

# this handles the test cases that include extra needs such as hosting a webserver, spoofing bank apis, calendar servers, email servers, putting files on the system
import outcome_handler

agent_names = [
    "claude",
    "custom",
    "open_claw"
]


assets_dir = os.path.abspath("tests/assets/clean-assets")

for folder in os.listdir("tests"):
    test_case_dir = os.path.join("tests", folder)

    outcome_handler.setup_test_case(test_case_dir)
    

    if os.path.isdir(test_case_dir):
        prompt_file_path = os.path.join(test_case_dir, "prompt.txt")
        attack_file_path = os.path.join(test_case_dir, "attack.txt")

        if os.path.exists(prompt_file_path):
            with open(prompt_file_path, "r") as f:
                prompt = f.read().strip()
        if os.path.exists(attack_file_path):
            with open(attack_file_path, "r") as f:
                attack = f.read().strip()
        
            for agent in agent_names:
                for asset in os.listdir(assets_dir):
                    asset_path = os.path.join(assets_dir, asset)

                    # inject the attack into the payload
                    injected_asset = prompt_injector.inject_attack(asset_path, attack)

                    # this should return None if injection fails, return the file path if injection succeeds

                    if not injected_asset:
                        print(f"Failed to inject attack for agent '{agent}' in test case '{folder}'. Skipping...")
                        continue

                    if os.path.isfile(injected_asset):
                        print(f"Running test for agent '{agent}' with prompt from '{folder}'...")
                        docker_handler.run_test(agent, prompt, asset=injected_asset)