import json

from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from risk_scorer import RiskScorer
from pipeline import extract_all_constraints


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(dataset_path):

    dataset = load_dataset(dataset_path)

    extractor = ConstraintExtractor()
    checker = ConsistencyChecker()
    scorer = RiskScorer()

    correct = 0
    total = len(dataset)

    mistakes = []

    for case in dataset:

        evidence_constraints = extract_all_constraints(
            extractor,
            case["evidence"]
        )

        answer_constraints = extract_all_constraints(
            extractor,
            case["answer"]
        )

        result = checker.check(
            evidence_constraints,
            answer_constraints
        )

        risk = scorer.score(result)

        # Our system's prediction:
        # if it found a contradiction -> RISKY, else -> RELIABLE
        predicted_label = "RISKY" if result["contradiction"] else "RELIABLE"

        expected_label = case["label"]

        is_correct = predicted_label == expected_label

        if is_correct:
            correct += 1
        else:
            mistakes.append({
                "id": case["id"],
                "constraint_type": case["constraint_type"],
                "expected": expected_label,
                "predicted": predicted_label,
                "result_type": result["type"],
                "risk_score": risk["risk_score"],
                "question": case["question"],
                "evidence": case["evidence"],
                "answer": case["answer"]
            })

    accuracy = correct / total

    print("=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print(f"Total cases: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.2%}")

    if mistakes:
        print(f"\nMISTAKES ({len(mistakes)}):")
        for m in mistakes:
            print("-" * 60)
            print("ID:", m["id"])
            print("Type:", m["constraint_type"])
            print("Expected:", m["expected"], "| Predicted:", m["predicted"])
            print("Checker result:", m["result_type"])
            print("Question:", m["question"])
            print("Evidence:", m["evidence"])
            print("Answer:", m["answer"])
    else:
        print("\nNo mistakes! All cases classified correctly.")

    return accuracy, mistakes


if __name__ == "__main__":
    run_benchmark("data/benchmark_dataset.json")