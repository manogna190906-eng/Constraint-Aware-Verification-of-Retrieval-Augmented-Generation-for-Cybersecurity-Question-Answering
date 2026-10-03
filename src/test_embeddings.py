from sentence_transformers import SentenceTransformer
import numpy as np


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


sentences = [
    "Successful exploitation requires administrator privileges.",
    "Only an administrator can perform this attack.",
    "The vulnerability affects versions 2.0 through 2.5.",
]


embeddings = model.encode(
    sentences,
    normalize_embeddings=True
)


similarity_1_2 = np.dot(embeddings[0], embeddings[1])
similarity_1_3 = np.dot(embeddings[0], embeddings[2])


print("Similarity between sentence 1 and 2:", similarity_1_2)
print("Similarity between sentence 1 and 3:", similarity_1_3)