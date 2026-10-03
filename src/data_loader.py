import json
from pathlib import Path


def load_documents(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with path.open("r", encoding="utf-8") as file:
        documents = json.load(file)

    if not isinstance(documents, list):
        raise ValueError("Expected the JSON file to contain a list.")

    return documents


if __name__ == "__main__":
    documents = load_documents("data/cybersecurity_documents.json")

    print(f"Loaded {len(documents)} documents.")

    for document in documents:
        print(f"{document['id']}: {document['title']}")