# YuHeng 900-record public subset

This directory contains a privacy-first, auditable subset of 900 image--text
records selected from the standardized 5,984-record YuHeng benchmark.

## Release summary

- 900 records and 900 referenced images.
- 225 records per domain.
- All 36 `domain × Lv × Lt` cells are represented.
- Every record satisfies `GT = max(Lv, Lt, La)` under
  `Normal < Suggestive < Violation`.
- Final labels: 447 `Violation` and 453 `Suggestive`.
- Association labels: 80 `Violation` and 820 `Normal`.
- 900 unique SHA-256 media hashes.
- No exact, near-perceptual, or full semantic duplicates reported by the saved
  release audit.
- All release images were re-encoded without EXIF and are below 8 MiB.
- The saved final Vision audit reports 900/900 processed, no errors, no
  configured identifier-pattern flags, and no detected faces.

Automated checks reduce privacy risk but do not prove that every visual or
contextual identifier is absent. Human review and the data-use restrictions
remain necessary.

## Files

- `dataset.jsonl`: all 900 records.
- `schema.json`: Draft 2020-12 schema for one release record.
- `data/<domain>/dataset.json`: the same records grouped by domain.
- `data/<domain>/images/`: release images named by anonymous `global_id`.
- `SCHEMA.md`: fields and strict label semantics.
- `SELECTION.md`: selection and privacy gates.
- `SPLITS.md`: relationship to the complete benchmark.
- `LABEL_PROVENANCE.md`: retained and unavailable label evidence.
- `DATA_USE_POLICY.md`: permitted and prohibited uses.
- `stats/`: saved selection, schema, privacy, duplicate, and integrity reports.
- `scripts/`: release construction and verification utilities.

## Declared source-metadata exception

`YuHeng-004480` is the only source record in the
`socio_economic / Lv=Violation / Lt=Normal` cell. Its source image carried
`AIGC Label=1` metadata. It is retained to preserve all 36 cells and is marked
by `media.source_aigc_label_1=true`. The release image was re-encoded without
that embedded metadata; the provenance flag remains visible.

No other selected record carries this source marker.

## Label-provenance limitation

The standardized source folders retain adjudicated `Lv` and `Lt`, but not one
unified original per-rater ballot export for `La`. Each released record exposes
this limitation through
`label_provenance.per_rater_La_ballots_retained=false`. This artifact must not
be described as providing per-rater `La` agreement evidence.

## Use

This subset supports artifact inspection and defensive safety evaluation.
Read the [data use policy](DATA_USE_POLICY.md) before use. The full benchmark
follows the [controlled-access plan](../documentation/FULL_DATASET_ACCESS.md).
