import os
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from email.utils import getaddresses
import pymupdf

from groq import Groq
import requests
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
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    sender = os.getenv("SMTP_FROM", "testbed@example.invalid")

    if not host or not port:
        return "Error: SMTP service is not configured."

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = "Testbed message"
    email.set_content(message)

    try:
        with smtplib.SMTP(host, int(port), timeout=10) as smtp:
            smtp.send_message(email)
    except (OSError, smtplib.SMTPException, ValueError) as error:
        return f"Error sending message: {error}"

    print(f"\n[EMAIL SENT]\nTo: {recipient}\nMessage: {message}")
    return f"Message sent to {recipient}."


def fetch_emails(limit: int = 10) -> str:
    """Retrieve recent captured emails from the configured Mailpit API."""
    api_url = os.getenv("MAILPIT_API_URL")
    if not api_url:
        return "Error: Email service is not configured."

    try:
        response = requests.get(
            f"{api_url.rstrip('/')}/messages",
            params={"limit": max(1, min(limit, 50))},
            timeout=10,
        )
        response.raise_for_status()
        messages = response.json().get("messages", [])
        if not messages:
            return "No emails found."

        results = []
        for summary in messages:
            message_id = summary.get("ID") or summary.get("ID".lower())
            if not message_id:
                continue

            detail = requests.get(
                f"{api_url.rstrip('/')}/message/{message_id}",
                timeout=10,
            )
            detail.raise_for_status()
            email = detail.json()
            recipients = getaddresses(
                email.get("To", []) if isinstance(email.get("To"), list)
                else [email.get("To", "")]
            )
            results.append(
                "\n".join(
                    [
                        f"From: {email.get('From', '')}",
                        f"To: {', '.join(address for _, address in recipients)}",
                        f"Subject: {email.get('Subject', '')}",
                        f"Date: {email.get('Date', '')}",
                        f"Body:\n{email.get('Text', '')}",
                    ]
                )
            )

        return "\n\n--- EMAIL ---\n\n".join(results) or "No emails found."
    except (OSError, requests.RequestException, ValueError) as error:
        return f"Error retrieving emails: {error}"


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


def execute_code(code: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            return f"Error executing code: {result.stderr.strip()}"

        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error executing code: execution timed out."
    except Exception as e:
        return f"Error executing code: {e}"
