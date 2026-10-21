import docker_handler
import os

agent_names = [
    "claude",
    "custom",
    "open_claw"
]

for folder in os.listdir("tests"):
    test_case_dir = os.path.join("tests", folder)
    if os.path.isdir(test_case_dir):
        prompt_file_path = os.path.join(test_case_dir, "prompt.txt")
        assets_dir = os.path.join(test_case_dir, "assets")
        if os.path.exists(prompt_file_path):
            with open(prompt_file_path, "r") as f:
                prompt = f.read().strip()
            for agent in agent_names:
                print(f"Running test for agent '{agent}' with prompt from '{folder}'...")
                docker_handler.run_test(agent, prompt, test_case_dir=assets_dir)