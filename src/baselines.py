from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def extract_all_constraints(extractor, text, enabled_types=None):
    """
    Same helper as in pipeline.py, with an added enabled_types filter
    used only for the ablation study (evaluate the system with one
    constraint type's extraction switched off).
    """
    constraints = []
    constraints.extend(extractor.extract_negation(text))
    constraints.extend(extractor.extract_prerequisites(text))
    constraints.extend(extractor.extract_conditions(text))
    constraints.extend(extractor.extract_versions(text))

    if enabled_types is not None:
        constraints = [c for c in constraints if c["type"] in enabled_types]

    return constraints


class NoCheckBaseline:
    """
    Baseline 1: plain RAG with no reliability layer.
    Always predicts RELIABLE. Establishes the base rate.
    """

    def predict(self, evidence_text, answer_text):
        return "RELIABLE"


class GenericSimilarityBaseline:
    """
    Baseline 2: generic semantic-similarity-only checker.
    No constraint extraction, no polarity awareness — just compares
    overall evidence-vs-answer similarity using the same embedding
    model as the real system, and flags RISKY if similarity falls
    below a threshold.
    """

    def __init__(self, threshold=0.45):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.threshold = threshold

    def similarity(self, text1, text2):
        embeddings = self.model.encode([text1, text2])
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    def predict(self, evidence_text, answer_text):
        score = self.similarity(evidence_text, answer_text)
        return "RISKY" if score < self.threshold else "RELIABLE"


class ConstraintAwarePredictor:
    """
    Wraps the real extractor + checker (used exactly as-is, unmodified)
    into a predict(evidence_text, answer_text) -> RELIABLE/RISKY
    interface, for apples-to-apples comparison with the baselines.

    enabled_types: which constraint types to extract/check, for the
    ablation study. None = all four types (the full system).
    """

    def __init__(self, extractor, checker, enabled_types=None):
        self.extractor = extractor
        self.checker = checker
        self.enabled_types = enabled_types

    def predict(self, evidence_text, answer_text):
        evidence_constraints = extract_all_constraints(self.extractor, evidence_text, self.enabled_types)
        answer_constraints = extract_all_constraints(self.extractor, answer_text, self.enabled_types)
        result = self.checker.check(evidence_constraints, answer_constraints)
        return "RISKY" if result["contradiction"] else "RELIABLE"