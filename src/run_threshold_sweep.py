import json

from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from baselines import ConstraintAwarePredictor


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
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}


def run_at_threshold(dataset, extractor, threshold):
    checker = ConsistencyChecker(threshold=threshold)
    system = ConstraintAwarePredictor(extractor, checker)
    predictions = [system.predict(c["evidence"], c["answer"]) for c in dataset]
    labels = [c["label"] for c in dataset]
    return compute_metrics(predictions, labels)


if __name__ == "__main__":

    full_dataset = load_dataset("data/benchmark_dataset_v2.json")

    dev_dataset = [c for c in full_dataset if int(c["id"].replace("BM", "")) <= 30]
    secondary_dataset = [c for c in full_dataset if int(c["id"].replace("BM", "")) >= 31]

    print(f"Development set (BM001-030): {len(dev_dataset)} cases")
    print(f"Secondary set (BM031-080): {len(secondary_dataset)} cases")
    print(f"Full set: {len(full_dataset)} cases\n")

    extractor = ConstraintExtractor()

    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]

    print("=" * 70)
    print("THRESHOLD SWEEP ON DEVELOPMENT SET ONLY (BM001-030)")
    print("=" * 70)

    best_threshold = None
    best_f1 = -1
    sweep_results = {}

    for t in thresholds:
        m = run_at_threshold(dev_dataset, extractor, t)
        sweep_results[t] = m
        print(f"tau={t:.2f}  acc={m['accuracy']*100:5.1f}%  prec={m['precision']*100:5.1f}%  "
              f"rec={m['recall']*100:5.1f}%  f1={m['f1']*100:5.1f}%")
        if m["f1"] > best_f1:
            best_f1 = m["f1"]
            best_threshold = t

    print(f"\nBest threshold selected on DEV SET ONLY: tau = {best_threshold}")

    print("\n" + "=" * 70)
    print(f"APPLYING tau = {best_threshold} (chosen on dev set) TO FULL AND SECONDARY SETS")
    print("=" * 70)

    m_full = run_at_threshold(full_dataset, extractor, best_threshold)
    print(f"\nFULL (N=80) at tau={best_threshold}:")
    print(f"  Accuracy: {m_full['accuracy']*100:.2f}%  Precision: {m_full['precision']*100:.2f}%  "
          f"Recall: {m_full['recall']*100:.2f}%  F1: {m_full['f1']*100:.2f}%")

    m_secondary = run_at_threshold(secondary_dataset, extractor, best_threshold)
    print(f"\nSECONDARY (N=50) at tau={best_threshold}:")
    print(f"  Accuracy: {m_secondary['accuracy']*100:.2f}%  Precision: {m_secondary['precision']*100:.2f}%  "
          f"Recall: {m_secondary['recall']*100:.2f}%  F1: {m_secondary['f1']*100:.2f}%")

    print("\n" + "=" * 70)
    print("SWEEP SUMMARY (development set)")
    print("=" * 70)
    print(f"{'tau':<8}{'Acc':>8}{'Prec':>8}{'Rec':>8}{'F1':>8}")
    for t in thresholds:
        m = sweep_results[t]
        marker = "  <-- selected" if t == best_threshold else ""
        print(f"{t:<8.2f}{m['accuracy']*100:>7.1f}%{m['precision']*100:>7.1f}%{m['recall']*100:>7.1f}%{m['f1']*100:>7.1f}%{marker}")