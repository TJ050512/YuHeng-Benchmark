# Reproducibility scope

This artifact supports deterministic inspection of the released dataset and
reference metrics. It does not claim full replay of historical model API runs.

## Directly reproducible

The repository supports the following checks:

- inspect 900 structured image--text records and their media;
- validate record count, IDs, domains, labels, and maximum-risk aggregation;
- check that referenced images exist and match their recorded SHA-256 values;
- inspect the complete record schema and saved release audits;
- run the structured-output parser tests; and
- recompute VR, IVA, SCAS, and MER from aligned, label-complete structured
  predictions.

## Required for a new model run

A new evaluation should archive:

- the exact system and user prompts;
- provider, model name, and model revision;
- decoding and sampling parameters;
- raw model responses;
- retry, refusal, and parsing-failure records;
- the parser version and normalization map; and
- the exact gold-data and prediction files used for scoring.

The command-line evaluator consumes structured JSONL. It does not call model
APIs or silently convert failed responses into valid labels.

## Historical evidence not retained

This repository does not contain the original:

- raw model responses;
- rendered per-model requests;
- model revisions and decoding parameters;
- retry, refusal, and parser logs;
- MIS judge outputs; or
- MIS human-validation records.

Consequently, the paper's historical result tables cannot be reconstructed from
raw responses using this repository alone. The included flag accounting and
parser contract are intended for transparent future runs.

## Annotation evidence boundary

The standardized data do not include one unified original per-rater `La`
ballot export or a complete adjudication log. Record-level labels remain
inspectable, but per-rater `La` agreement cannot be recomputed from this
artifact.

