# Evaluation and reproducibility

Python 3.10 or newer is required.

Install the reference evaluator:

```bash
python -m pip install -e evaluation
python -m unittest discover -s evaluation/tests -v
```

## Prediction format

Evaluate aligned JSONL files:

```bash
yuheng-eval --gold path/to/gold.jsonl --predictions path/to/predictions.jsonl
```

Supply one prediction per gold record in the same order. Each line contains
`level_of_picture`, `level_of_word`, `final_risk_label`, and
`cross_modal_safety`. Use `Normal`, `Suggestive`, or `Violation` for the label
fields and `Yes` or `No` for the cross-modal flag.

The evaluator reports violation recall (VR), implicit violation attenuation
(IVA), SCAS, MER, and the cardinality of each metric set. SCAS uses the paper's
`I` versus `not I` comparison, while MER is evaluated on the paper's
unimodal-nonviolation set `M`; both denominators are stated explicitly in the
implementation. For label-complete structured prediction rows, optional
boolean `refusal` and `parsing_failure` flags are counted and reported.

The CLI consumes already structured, label-complete JSONL. It does not ingest
raw response text or automatically turn parser exceptions or refusals into
flagged prediction rows. The separately exposed `parse_model_output` library
function validates raw text when called by an external runner. An end-to-end
adapter and an explicit scoring policy for failed or refused rows are still
required for a new raw-response pipeline.

## Prompt artifacts and parser contract

[Section D.1 of the included supplementary document](../supplement.pdf) prints
the structured inference prompt. The [`prompts/`](prompts/) directory also
contains:

- a [machine-readable documentary transcription](prompts/appendix_prompt_transcription.json)
  that preserves the printed keys, legacy labels, ordering, and wording; and
- a [canonical normalized reference](prompts/canonical_normalized_reference.json)
  for future adapters using `Normal`, `Suggestive`, and `Violation`.

The distinction is intentional: the first records what is visibly printed in
the included supplement, while the second is a forward-looking compatibility
artifact. Neither is a retained historical API request. The reference parser
accepts documented space/underscore key aliases and historical label aliases,
including `Teasing`, `Soft_Porn`, and `Illegal`, and requires all six prompt
fields: modality labels, association, vague method, cross-modal flag, and final
label. It raises an explicit error for malformed JSON, missing required fields,
invalid labels, invalid vague-method values, or invalid Yes/No flags. It does
not enforce printed key order, Simplified-Chinese sentence count, or semantic
consistency among predicted fields; field inconsistency remains model behavior
for the diagnostic metrics to measure rather than a parsing precondition.

Appendix D.2 reports up to three retries for malformed or schema-invalid JSON.
Remaining parse failures count as incorrect non-violation predictions. Generic
refusals are tracked separately and map to Violation and cross-modal activation
only in the refusal-aware analysis. The CLI scores rows already prepared under
the chosen protocol. The reference parser is available to external runners.

Raw model outputs, retry counts, parser failures, refusals, rendered prompts,
model revisions, and decoding parameters must accompany any reproduced table.
This repository does not contain the original model outputs, so the published
paper numbers cannot be re-evaluated from raw responses. The flag-based
accounting hooks cannot reconstruct empirical rates from absent historical
responses.

## Scope of MIS

MIS is retained only as an exploratory analysis. It is not implemented by this
reference evaluator and is not used as validation evidence for the released
dataset or for the deterministic SCAS/MER calculations. Because the original
MIS judge outputs and human-validation records were not retained, this artifact
neither validates nor reproduces MIS. Any future quantitative use must report
the judge prompt, judge model and revision, raw judge outputs, a human-validation
sample, and human--judge agreement statistics.

## Original-run evidence boundary

API billing records can corroborate paid access to a service, but they cannot
establish the prompts, model revisions, decoding settings, raw outputs,
refusals, retries, parser outcomes, or reported metrics. Reproducibility requires records of the evaluation runs.
