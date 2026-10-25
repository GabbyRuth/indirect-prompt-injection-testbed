import os
from groq import Groq
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
OUTPUT_DIR = BASE_DIR / "output"

def read_file(filename: str) -> str:
    try:
        file_path = (DOCUMENTS_DIR / filename).resolve()

        # prevent agent from reading outside documents
        if not file_path.is_relative_to(DOCUMENTS_DIR.resolve()):
            return "Error: Access denied."

        if not file_path.is_file():
            return f"Error: File '{filename}' not found."

        return file_path.read_text(encoding="utf-8")

    except Exception as e:
        return f"Error reading file: {e}"


def summarize_document(filename: str) -> str:
    content = read_file(filename)

    if content.startswith("Error:"):
        return content

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {
                "role": "system",
                "content": "Summarize the provided document accurately and concisely."
            },
            {
                "role": "user",
                "content": f"Summarize this document:\n\n{content}"
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content or ""


def search_local_docs(query: str) -> str:
    matches = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append(
                    f"{file_path.name}, line {line_number}: {line}"
                )

    if not matches:
        return f"No results found for '{query}'."

    return "\n".join(matches)

# TODO: Potentially implement search_web

def send_message(recipient: str, message: str) -> str:
    print(f"\n[SIMULATED MESSAGE]")
    print(f"To: {recipient}")
    print(f"Message: {message}")

    return f"Simulated message sent to {recipient}."


def write_file(filename: str, content: str) -> str:
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        file_path = (OUTPUT_DIR / filename).resolve()

        if not file_path.is_relative_to(OUTPUT_DIR.resolve()):
            return "Error: Access denied."

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return f"Successfully wrote to {filename}."

    except Exception as e:
        return f"Error writing file: {e}"