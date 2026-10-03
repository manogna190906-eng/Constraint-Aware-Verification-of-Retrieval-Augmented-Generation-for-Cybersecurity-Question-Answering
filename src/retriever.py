from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class Retriever:
    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Load the pretrained embedding model.

        The model converts text into numerical vectors.
        """
        self.model = SentenceTransformer(model_name)

        self.documents = []
        self.embeddings = None
        self.index = None

    def load_documents(self, file_path):
        """
        Load cybersecurity documents from a JSON file.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document file not found: {file_path}"
            )

        with path.open("r", encoding="utf-8") as file:
            self.documents = json.load(file)

        if not isinstance(self.documents, list):
            raise ValueError(
                "Expected the JSON file to contain a list."
            )

        print(
            f"Loaded {len(self.documents)} documents."
        )

    def build_index(self):
        """
        Convert documents into embeddings
        and store them inside a FAISS index.
        """

        if not self.documents:
            raise ValueError(
                "No documents loaded."
            )

        texts = [
            document["text"]
            for document in self.documents
        ]

        print("Creating embeddings...")

        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        self.embeddings = self.embeddings.astype(
            "float32"
        )

        dimension = self.embeddings.shape[1]

        print(
            f"Embedding dimension: {dimension}"
        )

        # Because embeddings are normalized,
        # inner product is equivalent to cosine similarity.
        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(self.embeddings)

        print(
            f"FAISS index contains "
            f"{self.index.ntotal} vectors."
        )

    def search(self, query, top_k=3):
        """
        Search for the most relevant documents
        for the given query.
        """

        if self.index is None:
            raise RuntimeError(
                "FAISS index has not been built."
            )

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        query_embedding = query_embedding.astype(
            "float32"
        )

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):
            if index == -1:
                continue

            results.append(
                {
                    "document": self.documents[index],
                    "score": float(score)
                }
            )

        return results


if __name__ == "__main__":

    retriever = Retriever()

    retriever.load_documents(
        "data/cybersecurity_documents.json"
    )

    retriever.build_index()

    question = input(
        "\nEnter a cybersecurity question: "
    )

    results = retriever.search(
        question,
        top_k=3
    )

    print("\nTop relevant documents:\n")

    for i, result in enumerate(
        results,
        start=1
    ):
        document = result["document"]
        score = result["score"]

        print(
            f"{i}. {document['id']} "
            f"(score={score:.4f})"
        )

        print(
            document["text"]
        )

        print("-" * 60)