from retriever import Retriever
from generator import LLMGenerator


retriever = Retriever()

retriever.load_documents(
    "data/cybersecurity_documents.json"
)

retriever.build_index()


question = input(
    "Enter a cybersecurity question: "
)

retrieved_documents = retriever.search(
    question,
    top_k=3
)


print("\nRetrieved evidence:\n")

for item in retrieved_documents:
    document = item["document"]
    score = item["score"]

    print(
        f"{document['id']} "
        f"(score={score:.4f})"
    )

    print(document["text"])
    print("-" * 60)


generator = LLMGenerator()

answer = generator.generate(
    question,
    retrieved_documents
)


print("\nLLM Answer:\n")
print(answer)