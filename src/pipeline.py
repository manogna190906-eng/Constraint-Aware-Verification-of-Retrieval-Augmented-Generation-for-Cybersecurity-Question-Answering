from retriever import Retriever
from generator import LLMGenerator
from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from risk_scorer import RiskScorer


def extract_all_constraints(extractor, text):
    """
    Run all four constraint extractors on a piece of text
    and combine the results into one list.
    """

    constraints = []

    constraints.extend(extractor.extract_negation(text))
    constraints.extend(extractor.extract_prerequisites(text))
    constraints.extend(extractor.extract_conditions(text))
    constraints.extend(extractor.extract_versions(text))

    return constraints


def run_pipeline(question, retriever, generator, extractor, checker, scorer, top_k=3):
    """
    Run the full constraint-aware RAG reliability pipeline
    on a single question.
    """

    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("=" * 70)

    # Step 1: Retrieve evidence
    results = retriever.search(question, top_k=top_k)

    if not results:
        print("\nNo evidence retrieved. Cannot answer.")
        return

    print("\nRETRIEVED EVIDENCE:")

    evidence_texts = []

    for i, result in enumerate(results, start=1):
        document = result["document"]
        score = result["score"]

        print(f"{i}. {document['id']} (score={score:.4f})")
        print(document["text"])
        print("-" * 60)

        evidence_texts.append(document["text"])

    combined_evidence = "\n".join(evidence_texts)

    # Step 2: Generate an answer
    answer = generator.generate(question, results)

    print("\nGENERATED ANSWER:")
    print(answer)

    # Step 3: Extract constraints from evidence and answer
    evidence_constraints = extract_all_constraints(
        extractor,
        combined_evidence
    )

    answer_constraints = extract_all_constraints(
        extractor,
        answer
    )

    print("\nEVIDENCE CONSTRAINTS:")
    print(evidence_constraints)

    print("\nANSWER CONSTRAINTS:")
    print(answer_constraints)

    # Step 4: Check consistency
    result = checker.check(
        evidence_constraints,
        answer_constraints
    )

    print("\nRELIABILITY VERDICT:")
    print("Result:", result["type"])
    print("Risk:", result["risk"])

    if result["contradiction"]:

        print("\nWHY?")
        print("Evidence:", result["evidence_constraint"])
        print("Answer:", result["answer_constraint"])

    # Step 5: Score the risk
    risk = scorer.score(result)

    print("\nRISK SCORE:")
    print("Score:", risk["risk_score"])
    print("Level:", risk["risk_level"])
    print("Base severity:", risk["base_severity"])
    print("Confidence:", risk["confidence"])

    return result, risk


if __name__ == "__main__":

    retriever = Retriever()
    retriever.load_documents("data/cybersecurity_documents.json")
    retriever.build_index()

    generator = LLMGenerator()
    extractor = ConstraintExtractor()
    checker = ConsistencyChecker()
    scorer = RiskScorer()

    question = input("\nEnter a cybersecurity question: ")

    run_pipeline(
        question,
        retriever,
        generator,
        extractor,
        checker,
        scorer
    )