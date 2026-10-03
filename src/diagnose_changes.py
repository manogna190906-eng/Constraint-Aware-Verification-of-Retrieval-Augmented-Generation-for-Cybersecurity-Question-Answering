import json

from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from baselines import ConstraintAwarePredictor


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":

    dataset = load_dataset("data/benchmark_dataset_v2.json")

    extractor = ConstraintExtractor()
    checker = ConsistencyChecker()
    system = ConstraintAwarePredictor(extractor, checker)

    newly_caught = []
    false_positives = []
    still_missed = []

    for case in dataset:
        prediction = system.predict(case["evidence"], case["answer"])
        expected = case["label"]

        if prediction == expected:
            continue  # correct, nothing interesting to report

        if expected == "RISKY" and prediction == "RELIABLE":
            still_missed.append(case)
        elif expected == "RELIABLE" and prediction == "RISKY":
            false_positives.append(case)

    print("=" * 60)
    print(f"FALSE POSITIVES ({len(false_positives)}) — flagged RISKY but actually RELIABLE")
    print("=" * 60)
    for c in false_positives:
        print(f"\n{c['id']} [{c['constraint_type']}]")
        print(f"  Evidence: {c['evidence']}")
        print(f"  Answer:   {c['answer']}")

    print("\n" + "=" * 60)
    print(f"STILL MISSED ({len(still_missed)}) — genuinely RISKY but predicted RELIABLE")
    print("=" * 60)
    for c in still_missed:
        print(f"\n{c['id']} [{c['constraint_type']}]")
        print(f"  Evidence: {c['evidence']}")
        print(f"  Answer:   {c['answer']}")