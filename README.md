# Constraint-Aware RAG Reliability for Cybersecurity QA

A reliability verification layer for Retrieval-Augmented Generation (RAG) systems in cybersecurity question answering. Retrieving the correct evidence doesn't guarantee an LLM's answer actually respects it — this project detects when a generated answer **silently contradicts** the security-critical logic in its own retrieved evidence (e.g. flipping "cannot execute the attack" into "can execute the attack").

## The problem

A RAG system can retrieve the right vulnerability advisory and still generate a wrong answer — reversing a negation, dropping a prerequisite, ignoring a conditional clause, or misreporting a version's patch status. Standard RAG pipelines have no way to catch this. This project adds a verification layer that does.

## How it works

1. **Retrieve** — FAISS + SentenceTransformer (`all-MiniLM-L6-v2`) embeddings pull the most relevant evidence for a question.
2. **Generate** — an LLM (OpenAI API) answers the question conditioned on that evidence.
3. **Extract** — a rule-based extractor pulls four types of safety-critical constraints from *both* the evidence and the answer:
   - **Negation** — can/cannot an actor do something
   - **Prerequisite** — what's required (or explicitly not required)
   - **Condition** — "only when X" / "except when X" clauses
   - **Version** — affected-range / patched / vulnerable status
4. **Check** — compares the two constraint sets using exact matching (versions) and embedding similarity (free text), flagging a contradiction when claims match but polarity differs.
5. **Score** — assigns a weighted risk score (LOW / MEDIUM / HIGH) combining contradiction severity with match confidence.

```
Question → Retriever → Evidence → LLM → Answer
                                           ↓
                        Constraint Extraction (Evidence AND Answer)
                                           ↓
                              Consistency Checker
                                           ↓
                               Risk Score → RELIABLE / RISKY
```

## Results

Evaluated on an 80-case manually-constructed benchmark (40 RELIABLE / 40 RISKY), with a 50-case secondary subset held apart from initial threshold tuning.

| Method | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| No-Check baseline (always "reliable") | 50.0% | 0.0% | 0.0% | 0.0% |
| Generic semantic-similarity baseline | 48.8% | 40.0% | 5.0% | 8.9% |
| **This system** | **91.25%** | **94.6%** | **87.5%** | **90.9%** |

A per-type ablation study shows removing any single constraint type drops accuracy by 7.5–11.3 percentage points — all four categories contribute meaningfully.

**Note:** this is a preliminary research system. The benchmark is manually authored (not sourced from real CVEs), built by the same authors who designed the extractor, without an independent annotator or a fully held-out test set. See the paper's limitations and future-work sections for the full picture.

## Project structure

```
src/
  retriever.py              # FAISS + embedding retrieval
  generator.py               # OpenAI API generation
  constraint_extractor.py    # rule-based 4-type constraint extraction
  consistency_checker.py     # contradiction detection + similarity matching
  risk_scorer.py             # weighted risk scoring
  baselines.py                # No-Check and Generic Similarity baselines
  pipeline.py                 # end-to-end: question → verdict
  run_full_evaluation.py      # evaluation + baselines + ablation
  run_holdout_evaluation.py   # secondary-subset evaluation
  run_threshold_sweep.py      # dev-set-only threshold selection
  diagnose_changes.py         # per-case error diagnostics
data/
  benchmark_dataset_v2.json   # 80-case labeled benchmark
  cybersecurity_documents.json
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Requires Python 3.11–3.13 (compiled dependencies such as NumPy and FAISS may not yet have stable wheels for the newest Python releases).

## Usage

```bash
# Run the full interactive pipeline
python src/pipeline.py

# Reproduce the benchmark evaluation
python src/run_full_evaluation.py

# Reproduce the threshold sensitivity sweep
python src/run_threshold_sweep.py
```

## Tech stack

Python · SentenceTransformers · FAISS · scikit-learn · OpenAI API

## Status

Preliminary research prototype. A full write-up (methodology, baselines, ablation, error analysis, and disclosed limitations) is included as an IEEE-format paper draft in this repo.

## License

Add a license of your choice (MIT is a common default for research code).
