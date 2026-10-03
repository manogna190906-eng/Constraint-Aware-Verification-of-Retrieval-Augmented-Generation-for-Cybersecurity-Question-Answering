import json

from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from baselines import NoCheckBaseline, GenericSimilarityBaseline, ConstraintAwarePredictor

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(predictions, labels):
    tp = sum(1 for p, l in zip(predictions, labels) if p == "RISKY" and l == "RISKY")
    fp = sum(1 for p, l in zip(predictions, labels) if p == "RISKY" and l == "RELIABLE")
    fn = sum(1 for p, l in zip(predictions, labels) if p == "RELIABLE" and l == "RISKY")
    tn = sum(1 for p, l in zip(predictions, labels) if p == "RELIABLE" and l == "RELIABLE")

    total = len(labels)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}


def run_method(predict_fn, dataset):
    predictions = [predict_fn(c["evidence"], c["answer"]) for c in dataset]
    labels = [c["label"] for c in dataset]
    return compute_metrics(predictions, labels)


def print_metrics(name, m):
    print(f"\n{name}")
    print(f"  Accuracy:  {m['accuracy']*100:.2f}%")
    print(f"  Precision: {m['precision']*100:.2f}%")
    print(f"  Recall:    {m['recall']*100:.2f}%")
    print(f"  F1:        {m['f1']*100:.2f}%")
    print(f"  TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}")


if __name__ == "__main__":

    dataset = load_dataset("data/benchmark_dataset_v2.json")
    print(f"Loaded {len(dataset)} cases.")

    extractor = ConstraintExtractor()

    # Baseline 1
    no_check = NoCheckBaseline()
    m1 = run_method(no_check.predict, dataset)
    print_metrics("BASELINE 1: No-Check (always RELIABLE)", m1)

    # Baseline 2 — calibrate threshold on this dataset rather than guessing
    print("\n--- Calibrating Baseline 2 threshold ---")
    calibration_model = GenericSimilarityBaseline(threshold=0.0)  # reuse its loaded model
    best_thresh, best_f1 = None, -1
    for thresh in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
        calibration_model.threshold = thresh
        m_try = run_method(calibration_model.predict, dataset)
        print(f"  threshold={thresh:.2f}  acc={m_try['accuracy']*100:.1f}%  f1={m_try['f1']*100:.1f}%")
        if m_try["f1"] > best_f1:
            best_f1 = m_try["f1"]
            best_thresh = thresh
    print(f"Best Baseline 2 threshold on this dataset: {best_thresh}\n")

    generic_sim = GenericSimilarityBaseline(threshold=best_thresh)
    m2 = run_method(generic_sim.predict, dataset)
    print_metrics(f"BASELINE 2: Generic Semantic Similarity (threshold={best_thresh})", m2)

    # Proposed system (full)
    checker = ConsistencyChecker()
    full_system = ConstraintAwarePredictor(extractor, checker)
    m_full = run_method(full_system.predict, dataset)
    print_metrics("PROPOSED: Constraint-Aware (all 4 types)", m_full)

    # Ablation
    print("\n" + "=" * 60)
    print("ABLATION STUDY")
    print("=" * 60)

    all_types = ["NEGATION", "PREREQUISITE", "CONDITION", "VERSION"]
    ablation_results = {}

    for removed_type in all_types:
        enabled = set(all_types) - {removed_type}
        checker_abl = ConsistencyChecker()
        ablated = ConstraintAwarePredictor(extractor, checker_abl, enabled_types=enabled)
        m_abl = run_method(ablated.predict, dataset)
        print_metrics(f"WITHOUT {removed_type}", m_abl)
        ablation_results[removed_type] = m_abl

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Method':<35}{'Acc':>8}{'Prec':>8}{'Rec':>8}{'F1':>8}")
    print(f"{'No-Check baseline':<35}{m1['accuracy']*100:>7.1f}%{m1['precision']*100:>7.1f}%{m1['recall']*100:>7.1f}%{m1['f1']*100:>7.1f}%")
    print(f"{'Generic similarity baseline':<35}{m2['accuracy']*100:>7.1f}%{m2['precision']*100:>7.1f}%{m2['recall']*100:>7.1f}%{m2['f1']*100:>7.1f}%")
    print(f"{'Constraint-Aware (full)':<35}{m_full['accuracy']*100:>7.1f}%{m_full['precision']*100:>7.1f}%{m_full['recall']*100:>7.1f}%{m_full['f1']*100:>7.1f}%")
    for t in all_types:
        m = ablation_results[t]
        print(f"{'  w/o ' + t:<35}{m['accuracy']*100:>7.1f}%{m['precision']*100:>7.1f}%{m['recall']*100:>7.1f}%{m['f1']*100:>7.1f}%")