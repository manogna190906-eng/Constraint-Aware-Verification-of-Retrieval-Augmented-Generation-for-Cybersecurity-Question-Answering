import os

from openai import OpenAI


class LLMGenerator:
    def __init__(self, model_name=None):
        """
        Initialize the OpenAI client.

        The API key is read from the OPENAI_API_KEY
        environment variable.

        The model name is read from OPENAI_MODEL
        unless one is passed explicitly.
        """

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set."
            )

        self.client = OpenAI(api_key=api_key)

        self.model_name = (
            model_name
            or os.getenv("OPENAI_MODEL")
        )

        if not self.model_name:
            raise RuntimeError(
                "OPENAI_MODEL environment variable is not set."
            )

    def generate(self, question, retrieved_documents):
        """
        Generate an answer using the user's question
        and the cybersecurity evidence retrieved by RAG.
        """

        if not retrieved_documents:
            raise ValueError(
                "No retrieved documents were provided."
            )

        # Convert retrieved documents into readable evidence.
        evidence_parts = []

        for item in retrieved_documents:
            document = item["document"]
            score = item["score"]

            evidence_parts.append(
                f"[{document['id']}] "
                f"(retrieval score: {score:.4f})\n"
                f"{document['text']}"
            )

        evidence = "\n\n".join(evidence_parts)

        # Prompt given to the LLM.
        prompt = f"""
You are a cybersecurity question-answering assistant.

Answer the user's question using ONLY the supplied evidence.

Important rules:
1. Do not invent facts.
2. Do not use information that is not supported by the evidence.
3. Preserve important conditions, negations, prerequisites,
   exceptions, and version restrictions from the evidence.
4. If the evidence is insufficient to answer the question,
   explicitly say that the evidence is insufficient.

Retrieved cybersecurity evidence:

{evidence}

User question:

{question}

Answer:
"""

        # Send the prompt to the OpenAI Responses API.
        response = self.client.responses.create(
            model=self.model_name,
            input=prompt
        )

        return response.output_text