# Dataset schema

YuHeng uses the ordered label set `Normal < Suggestive < Violation`.

- `Lv`: image-only label.
- `Lt`: text-only label.
- `La`: image-text association label.
- `GT`: final label. The paper defines `GT = max(Lv, Lt, La)`.
- `cross_modal_safety`: diagnostic flag indicating that composition adds risk.
- `association`: free-text rationale; it is not itself a categorical label.
- `implicit_mechanism`: polysemy, homophony, cultural allusion, visual
  euphemism, irony, or another documented mechanism.

Source-specific labels such as `Teasing`, `Soft_Porn`, `Soft Porn`, `Malicious`,
`Irritating`, `Illegal`, and `Insulting` are normalized by
`evaluation/src/yuheng_eval/labels.py`. The compact core JSON Schema is in
`documentation/core_schema.json`; the complete 900-record release schema is in
[`public_subset/schema.json`](../public_subset/schema.json).

## Provenance requirement

Every released categorical label must say whether it is an original annotator
decision, an adjudicated decision, or a deterministic derived field. Derived
labels must not be reported as independent human annotations.
