# Schema

Each line of `dataset.jsonl` is one image-text record.

The complete Draft 2020-12 machine-readable schema for one release record is
[`schema.json`](schema.json). The compact cross-version core schema is retained
at [`../documentation/core_schema.json`](../documentation/core_schema.json).
Record count, uniqueness, file
existence, media hashes, domain quotas, and duplicate/privacy gates are
collection-level constraints checked by `scripts/verify_release_v2.py`, not by
a single-record JSON Schema. All 900 records pass the complete schema; the saved
result is in [`stats/schema_validation_report.json`](stats/schema_validation_report.json).

| Field | Type | Meaning |
|---|---|---|
| `global_id` | string | Anonymous stable benchmark identifier. |
| `domain` | enum | One of the four YuHeng domains. |
| `domain_zh` | enum | Chinese name of the record's YuHeng domain. |
| `domain_en` | enum | English name of the record's YuHeng domain. |
| `text` | string | Textual modality. |
| `image_path` | string | Relative path to the release image. |
| `association` | string | Annotated image-text interpretation. |
| `implicit_mechanism` | string | Original mechanism string retained for provenance. |
| `mechanism_categories` | list | Normalized categories drawn from the six-category paper taxonomy. |
| `Lv` | enum | Visual-only safety label. |
| `Lt` | enum | Text-only safety label. |
| `La` | enum | Additional association safety level in the standardized export. |
| `GT` | enum | Strict final label. |
| `cross_modal_safety` | enum | Standardized `Yes`/`No` cross-modal indicator. |
| `cross_modal_emergent` | boolean | Whether the association adds risk beyond both isolated modalities. |
| `label_provenance` | object | Source/derivation disclosure, including ballot retention. |
| `media` | object | Hash, size, dimensions, privacy results, metadata stripping, and source AIGC provenance. |
| `selection` | object | Seed, quality score, privacy-first flag, and any declared exception. |

## Strict three-level rule

The ordered label set is:

`Normal < Suggestive < Violation`

The final label is always:

`GT = max(Lv, Lt, La)`

Thus `Lv=Normal, Lt=Suggestive, La=Normal` yields `GT=Suggestive`, not `Violation`.

## Normalized mechanism categories

- `semantic_polysemy`
- `homophonic_substitution`
- `cultural_allusion`
- `visual_euphemism`
- `sarcasm_irony`
- `other_implication`

A record may map to more than one normalized category. The original mechanism value is always preserved in `implicit_mechanism`.

## Association-label availability

The ordered schema permits all three values for `La`, but this 900-record
release contains 820 `Normal`, 80 `Violation`, and 0 `Suggestive` association
labels. This observed distribution must not be described as empirical
three-class agreement evidence. Any later reannotation is a separate post-hoc
audit and does not change the retained-original-ballot disclosure.
