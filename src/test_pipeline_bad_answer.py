from retriever import Retriever
from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from risk_scorer import RiskScorer
from pipeline import extract_all_constraints


retriever = Retriever()
retriever.load_documents("data/cybersecurity_documents.json")
retriever.build_index()

extractor = ConstraintExtractor()
checker = ConsistencyChecker()
scorer = RiskScorer()

question = "Is version 2.6 vulnerable to this attack?"

results = retriever.search(question, top_k=3)

evidence_texts = [r["document"]["text"] for r in results]
combined_evidence = "\n".join(evidence_texts)

print("RETRIEVED EVIDENCE:")
for r in results:
    print(r["document"]["id"], "-", r["document"]["text"])

# Deliberately WRONG answer, ignoring what the evidence says
bad_answer = "Yes, version 2.6 is vulnerable to the attack."

print("\nFORCED BAD ANSWER:")
print(bad_answer)

evidence_constraints = extract_all_constraints(extractor, combined_evidence)
answer_constraints = extract_all_constraints(extractor, bad_answer)

result = checker.check(evidence_constraints, answer_constraints)
risk = scorer.score(result)

print("\nRELIABILITY VERDICT:")
print("Result:", result["type"])
print("Risk:", result["risk"])

if result["contradiction"]:
    print("Evidence:", result["evidence_constraint"])
    print("Answer:", result["answer_constraint"])

print("\nRISK SCORE:")
print("Score:", risk["risk_score"])
print("Level:", risk["risk_level"])