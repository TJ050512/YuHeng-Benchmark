# Privacy and release controls

Anonymous repository hosting anonymizes repository ownership, not the contents
of binary images. A public full-media upload is therefore not a substitute for
controlled access to the complete benchmark.

The 900-record reviewer subset applies documented text-pattern, OCR, face,
metadata, size, and deduplication gates. The configured text patterns cover
emails, account handles, phone/ID/contact formats, and URLs; they do not prove
that every personal name or contextual identity clue is absent. Exact rules and
saved summaries are in `reviewer_subset/SELECTION.md` and
`reviewer_subset/stats/`.

Release images are re-encoded without EXIF, are below 8 MiB, and preserve a
per-record provenance flag for the declared source AIGC-metadata exception.
Automated OCR and face checks reduce risk but do not establish complete
anonymization. If a residual identifier is found, distribution of the affected
record should stop and its anonymous `global_id` should be reported.

The text-pattern helper in `tools/redact_text_identifiers.py` does not inspect
pixels. Copyright, platform terms, contextual privacy, and human review remain
release-owner responsibilities.
