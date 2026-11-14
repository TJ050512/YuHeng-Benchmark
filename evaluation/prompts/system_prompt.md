# Structured inference prompt artifacts

Appendix D.1 of the [camera-ready supplement](../../supplement.pdf) prints the structured inference prompt
used in the paper. The appendix contains
the prompt text, but it does not contain a separate prompt JSON file. To make
the printed material machine-readable without misrepresenting the historical
record, this directory now provides two distinct artifacts:

- [`appendix_prompt_transcription.json`](appendix_prompt_transcription.json) is
  a documentary transcription of the prompt printed in Appendix D.1. It
  preserves the printed key names, legacy label strings, key order, and the
  original `weather` typographical error. PDF line wrapping alone is
  normalized.
- [`canonical_normalized_reference.json`](canonical_normalized_reference.json)
  is a prospective reference prompt using the repository's canonical labels
  `Normal`, `Suggestive`, and `Violation`. It is derived from the appendix
  transcription and is intended for future adapters and reproducibility work.

The historical aliases map to the canonical release labels as follows:

| Printed appendix value | Canonical value |
|---|---|
| `Normal` | `Normal` |
| `Teasing` | `Suggestive` |
| `Soft_Porn` | `Suggestive` |
| `Suggestive` | `Suggestive` |
| `Illegal` | `Violation` |

Appendix D.2 describes up to three retries for malformed or schema-invalid
JSON and separate treatment of generic refusals. The original rendered
per-model requests, wrapper-specific image
placement, raw responses, retry/refusal/parser logs, model revisions, and
decoding settings were not retained. The transcription is therefore evidence
of the printed prompt. The exact provider-specific requests would require the
original logs.

For future or reproduced runs, model adapters should record the exact rendered
prompt, image-placement convention, model revision, decoding parameters, raw
response, retry count, parsing outcome, and refusal status. The released
reference parser validates all six required response fields, but the released
CLI still consumes already structured JSONL and does not implement an
end-to-end raw-response retry loop.
