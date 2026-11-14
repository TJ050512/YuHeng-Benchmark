# Selection and release gates

## Target

The target is 225 records per domain and 25 records per `Lv × Lt` cell. When a strict eligible cell contains fewer than 25 records, all eligible records are retained and the deficit is redistributed within the same domain. Exact counts are stored in `stats/selection_stats.json`.

## Pre-selection exclusions

- Missing, non-image, placeholder, or non-semantic media.
- Source records marked synthetic.
- Configured text patterns for emails, URLs, phone/ID/contact identifiers, or
  account handles. These rules do not guarantee removal of every personal name
  or contextual identity clue.
- Association explanations equal to a declared placeholder (for example,
  `字面意思` or `无`) or shorter than eight normalized characters.
- Missing mechanism annotations or declared placeholders such as `无`/`none`.
- Undecodable images, images smaller than 128 pixels on one side, and files over 8 MiB.
- Source images carrying `AIGC Label=1`, except the declared sole-cell record `YuHeng-004480`.

## Visual release gates

All strict candidates were scanned with macOS Vision accurate OCR using `zh-Hans` and `en-US`, plus face rectangle detection. Candidates were excluded for:

- account handles;
- mobile, ID-like, or long number patterns;
- URLs and contact hints;
- `IP属地` and profile/account fields;
- detected faces;
- Vision errors.

Selection then preferred longer text/association fields and mechanism diversity
through the documented heuristic score while enforcing unique exact media and
perceptual separation. This score is not a human semantic-quality rating.
Post-selection checks replaced one perceptual duplicate and one full semantic
duplicate. A final scan of the re-encoded 900 images found zero configured
risk-pattern flags, zero faces, and zero errors.

## Media processing

Every selected image was decoded, orientation-normalized, converted to a clean pixel representation, and re-encoded without EXIF. Media hashes and byte counts refer to the release copies, not the source files.

## Reproducibility

- Seed: `20260713`.
- Candidate and final statistics are included under `stats/`.
- Final validation is performed by `scripts/verify_release_v2.py` together with the saved Vision summary.
