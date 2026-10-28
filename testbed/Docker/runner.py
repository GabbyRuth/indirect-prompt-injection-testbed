# here we will read the env variables from docker, then run the agent with the prompt and test case dir
import os
import sys
import anthropic
from pathlib import Path

AGENT_NAME = os.getenv("AGENT_NAME")
PROMPT = os.getenv("PROMPT")

assets_dir = None

# check if theres assets in /app/assets

def load_assets():
    if Path("/app/assets").exists():
        global assets_dir
        assets_dir = "/app/assets"
        return assets_dir
    else:
        return None

def run_agent(agent_name, prompt, assets_dir=None):
    if agent_name == "claude":
        client = anthropic.Client(os.getenv("CLAUDE_API_KEY"))
        response = client.completions.create(
            model="claude-3-5-sonnet-latest",
            prompt=prompt,
            max_tokens_to_sample=1024
        )
        # return the response text and all actions taken by the agent in a structured format
        return response.completion



def main():
    if not AGENT_NAME or not PROMPT:
        print("AGENT_NAME and PROMPT environment variables must be set.")
        sys.exit(1)

    load_assets()
    result = run_agent(AGENT_NAME, PROMPT, assets_dir)
    print(f"=== Agent '{AGENT_NAME}' Execution Result ===")
    print(result)

if __name__ == "__main__":
    main()