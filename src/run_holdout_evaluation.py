import json

from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker
from baselines import NoCheckBaseline, GenericSimilarityBaseline, ConstraintAwarePredictor
from run_full_evaluation import compute_metrics, run_method, print_metrics


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":

    full_dataset = load_dataset("data/benchmark_dataset_v2.json")

    # Keep only the 50 cases NOT used during extractor/threshold tuning
    # (BM001-BM030 were the original development set; BM031-BM080 are new)
    holdout_dataset = [
        case for case in full_dataset
        if int(case["id"].replace("BM", "")) >= 31
    ]

    print(f"Full dataset: {len(full_dataset)} cases")
    print(f"Held-out dataset (BM031-BM080 only): {len(holdout_dataset)} cases")

    extractor = ConstraintExtractor()

    # No-Check baseline
    no_check = NoCheckBaseline()
    m1 = run_method(no_check.predict, holdout_dataset)
    print_metrics("HOLD-OUT: No-Check baseline", m1)

    # Generic Similarity baseline (reuse threshold already calibrated on full set = 0.65,
    # do NOT recalibrate on holdout — recalibrating here would itself be a form of leakage)
    generic_sim = GenericSimilarityBaseline(threshold=0.65)
    m2 = run_method(generic_sim.predict, holdout_dataset)
    print_metrics("HOLD-OUT: Generic Semantic Similarity (threshold=0.65, fixed from full-set calibration)", m2)

    # Proposed system (full, all 4 types) — the real test: unseen data, untouched thresholds
    checker = ConsistencyChecker()
    full_system = ConstraintAwarePredictor(extractor, checker)
    m_full = run_method(full_system.predict, holdout_dataset)
    print_metrics("HOLD-OUT: Constraint-Aware (all 4 types)", m_full)

    print("\n" + "=" * 60)
    print("HOLD-OUT SUMMARY (BM031-BM080, N=50, never used in tuning)")
    print("=" * 60)
    print(f"{'Method':<35}{'Acc':>8}{'Prec':>8}{'Rec':>8}{'F1':>8}")
    print(f"{'No-Check baseline':<35}{m1['accuracy']*100:>7.1f}%{m1['precision']*100:>7.1f}%{m1['recall']*100:>7.1f}%{m1['f1']*100:>7.1f}%")
    print(f"{'Generic similarity baseline':<35}{m2['accuracy']*100:>7.1f}%{m2['precision']*100:>7.1f}%{m2['recall']*100:>7.1f}%{m2['f1']*100:>7.1f}%")
    print(f"{'Constraint-Aware (full)':<35}{m_full['accuracy']*100:>7.1f}%{m_full['precision']*100:>7.1f}%{m_full['recall']*100:>7.1f}%{m_full['f1']*100:>7.1f}%")