from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"


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
