# YuHeng: MMAsia 2026 Anonymous Reviewer Artifact

This repository accompanies the anonymous MMAsia 2026 submission:

> **YuHeng: Benchmarking Implicit Multimodal Safety in Chinese High-Context Communication**

YuHeng is a diagnostic benchmark for safety risks whose meaning emerges from
Chinese image--text interaction rather than from an explicit cue in either
modality alone. The complete benchmark contains 5,984 image--text pairs in four
domains: sexual innuendo, gender bias, socio-economic controversies, and
geographic or cultural bias.

This repository is intended for double-blind artifact inspection. It contains a
privacy-filtered 900-record subset, the corresponding 900 media files,
machine-readable schemas, reference evaluation code, aggregate statistics, and
saved validation reports. It does not contain author names, affiliations,
reviewer correspondence, or links that identify the source repository.

## Repository contents

```text
.
├── README.md
├── reviewer_subset/       # 900 records, images, schema, and release evidence
├── evaluation/            # VR, IVA, SCAS, and MER reference implementation
├── documentation/         # annotation, schema, privacy, split, and access notes
└── tools/                 # dataset validation and statistics utilities
```

## Reviewer subset

The released inspection subset contains:

- 900 records and 900 referenced images;
- 225 records from each of the four domains;
- coverage of all 36 `domain × Lv × Lt` cells;
- 447 `Violation` and 453 `Suggestive` final labels;
- 900 unique release SHA-256 hashes;
- metadata-stripped images, each below 8 MiB; and
- saved OCR, face, duplicate, schema, and media-integrity audit summaries.

The subset is not a train/dev/test split and must not be used to tune systems
evaluated on YuHeng. It contains no `GT=Normal` records, so results calculated
only on this subset are not directly comparable with the full-benchmark results
reported in the paper.

See:

- [`reviewer_subset/README.md`](reviewer_subset/README.md)
- [`reviewer_subset/SELECTION.md`](reviewer_subset/SELECTION.md)
- [`reviewer_subset/SCHEMA.md`](reviewer_subset/SCHEMA.md)
- [`reviewer_subset/DATA_USE_POLICY.md`](reviewer_subset/DATA_USE_POLICY.md)

## Labels

YuHeng uses the ordered label set:

```text
Normal < Suggestive < Violation
```

For each item, `Lv`, `Lt`, and `La` denote the visual, textual, and associative
safety labels. The final benchmark label is:

```text
GT = max(Lv, Lt, La)
```

The operational annotation summary and evidence limitations are documented in
[`documentation/ANNOTATION_PROTOCOL.md`](documentation/ANNOTATION_PROTOCOL.md).

## Reference evaluator

Python 3.10 or newer is required. No third-party runtime dependency is needed.

```bash
python -m pip install -e evaluation
python -m unittest discover -s evaluation/tests -v
```

Evaluate aligned structured JSONL files with:

```bash
yuheng-eval --gold path/to/gold.jsonl --predictions path/to/predictions.jsonl
```

The evaluator implements violation recall (VR), implicit violation attenuation
(IVA), selective cross-modal activation score (SCAS), and metaphor emergence
ratio (MER). Its scope and retained-evidence boundary are described in
[`evaluation/README.md`](evaluation/README.md) and
[`documentation/REPRODUCIBILITY.md`](documentation/REPRODUCIBILITY.md).

## Quick integrity checks

From the repository root:

```bash
python tools/validate_dataset.py reviewer_subset/dataset.jsonl --expected-count 900
python tools/check_release.py
PYTHONPATH=evaluation/src python -m unittest discover -s evaluation/tests -v
```

`check_release.py` verifies the included image inventory, byte counts, SHA-256
values, per-domain JSON files, selection manifest, and label aggregation.
The release-construction scripts under
`reviewer_subset/scripts/` additionally document checks that require private
source records or saved Vision output; those external inputs are not published.
None of these scripts reconstructs historical model API responses.

## Complete benchmark

The full 5,984-record benchmark remains controlled because the source material
may be sensitive and may carry privacy, platform, copyright, or redistribution
constraints. If complete inspection is requested and MMAsia 2026 policy permits
it, access can be mediated through the official CMT or Program Chair channel.
Reviewers are not asked to contact the authors directly. See
[`documentation/FULL_DATASET_ACCESS.md`](documentation/FULL_DATASET_ACCESS.md).

## Evidence boundary

This artifact directly supports inspection of the released subset, its media,
schema, aggregate statistics, and deterministic evaluation implementation. It
does not contain:

- a unified original per-rater ballot export for `La`;
- complete adjudication logs;
- original raw model responses, retry/refusal/parser logs, or rendered
  provider-specific requests; or
- the original MIS judge outputs and human-validation records.

The repository therefore does not claim that the paper's historical model
tables can be replayed from raw responses. These limitations are stated
explicitly rather than reconstructed after the fact.

## Privacy, safety, and permitted use

The artifact contains sensitive social content. It is provided for confidential
peer review, defensive safety research, and reproducibility inspection only.
Users must not identify source-platform users, generate harmful content, train
systems to evade safety controls, or treat benchmark labels as legal judgments
or deployable moderation policy.

Automated privacy screening reduces risk but cannot prove that every identifier
is absent. Stop distribution of an affected record and report its anonymous
`global_id` through the official conference channel if a residual identifier is
found. No broad license to underlying source-platform media is implied.
