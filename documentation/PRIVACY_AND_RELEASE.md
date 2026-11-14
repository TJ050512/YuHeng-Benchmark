# Privacy and release controls

The public subset uses privacy-filtered media. The complete benchmark is planned
for [controlled access](FULL_DATASET_ACCESS.md) after publication.

The 900-record public subset applies documented text-pattern, OCR, face,
metadata, size, and deduplication gates. The configured text patterns cover
emails, account handles, phone/ID/contact formats, and URLs; they do not prove
that every personal name or contextual identity clue is absent. Exact rules and
saved summaries are in [selection notes](../public_subset/SELECTION.md) and
[saved audits](../public_subset/stats/).

Release images are re-encoded without EXIF, are below 8 MiB, and preserve a
per-record provenance flag for the declared source AIGC-metadata exception.
Automated OCR and face checks reduce risk but do not establish complete
anonymization. If a residual identifier is found, distribution of the affected
record should stop. Send its `global_id` to
[the corresponding author](mailto:qfang@bupt.edu.cn) without sharing the
identifier or the affected media publicly.

The text-pattern helper in `tools/redact_text_identifiers.py` does not inspect
pixels. Copyright, platform terms, contextual privacy, and human review remain
release-owner responsibilities.
