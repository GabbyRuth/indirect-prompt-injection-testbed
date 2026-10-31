import os
import pymupdf

from groq import Groq
from pathlib import Path
from bs4 import BeautifulSoup
from icalendar import Calendar

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
OUTPUT_DIR = BASE_DIR / "output"


def read_file(filename: str, documents_dir=None) -> str:
    try:
        directory = (
            Path(documents_dir)
            if documents_dir is not None
            else DOCUMENTS_DIR
        ).resolve()

        file_path = (directory / filename).resolve()

        if not file_path.is_relative_to(directory):
            return "Error: Access denied."

        if not file_path.is_file():
            return f"Error: File '{filename}' not found."

        extension = file_path.suffix.lower()

        if extension in (".txt", ".md"):
            return file_path.read_text(encoding="utf-8")

        elif extension == ".pdf":
            with pymupdf.open(file_path) as pdf:
                return "\n".join(
                    page.get_text() for page in pdf
                )

        elif extension == ".ics":
            calendar = Calendar.from_ical(file_path.read_bytes())
            results = []

            for event in calendar.walk("VEVENT"):
                for field in (
                    "SUMMARY",
                    "DESCRIPTION",
                    "LOCATION",
                    "DTSTART",
                    "DTEND",
                    "ORGANIZER",
                    "ATTENDEE",
                ):
                    values = event.get(field)

                    if values is None:
                        continue

                    if not isinstance(values, list):
                        values = [values]

                    for value in values:
                        results.append(f"{field}: {value}")

            return "\n".join(results)

        elif extension in (".html", ".htm"):
            html = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # Include page title and visible page text.
            for element in soup(["script", "style"]):
                element.decompose()

            return soup.get_text(separator="\n", strip=True)

        return f"Error: Unsupported file type '{extension}'."

    except Exception as e:
        return f"Error reading file: {e}"


def summarize_document(filename: str, documents_dir=None) -> str:
    content = read_file(filename, documents_dir=documents_dir)

    if content.startswith("Error:"):
        return content

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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


def search_local_docs(query: str, documents_dir=None) -> str:
    directory = (
        Path(documents_dir)
        if documents_dir is not None
        else DOCUMENTS_DIR
    ).resolve()

    matches = []

    for file_path in sorted(directory.iterdir()):
        if not file_path.is_file():
            continue

        content = read_file(
            file_path.name,
            documents_dir=directory
        )

        if content.startswith("Error:"):
            continue

        for line_number, line in enumerate(content.splitlines(), 1):
            if query.lower() in line.lower():
                matches.append(
                    f"{file_path.name}, line {line_number}: {line}"
                )

    if not matches:
        return f"No results found for '{query}'."

    return "\n".join(matches)


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