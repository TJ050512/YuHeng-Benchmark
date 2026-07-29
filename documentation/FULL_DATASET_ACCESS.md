# Controlled access to the complete YuHeng benchmark

## Purpose

The public MMAsia 2026 reviewer artifact contains 900 privacy-filtered
image--text records: 225 from each domain and coverage of all 36
`domain × Lv × Lt` cells. It represents approximately 15.0% of the complete
5,984-record YuHeng benchmark.

The complete dataset is not linked publicly because it contains sensitive
source-platform material and may be subject to privacy, platform, copyright,
and redistribution constraints.

## Review-stage procedure

If complete-benchmark inspection is necessary and MMAsia 2026 policy permits
it:

1. a reviewer, Area Chair, or Program Chair requests access through the
   official CMT or Program Chair channel;
2. the Program Chairs confirm that controlled access is compatible with the
   review policy without disclosing reviewer identity to the authors;
3. an anonymous, time-limited, read-only link is delivered through that
   official channel; and
4. access expires at the end of the authorized review period or at a time
   specified by the Program Chairs.

Reviewers are not asked to contact the authors directly. The authors must not
use access activity to infer reviewer identity.

No public or placeholder credential is stored in this repository.

## Material available for inspection

The controlled package may contain:

- all 5,984 standardized benchmark records;
- paired image--text material with available media-provenance disclosures;
- stable anonymous record identifiers;
- the four benchmark domains;
- visual (`Lv`), textual (`Lt`), associative (`La`), and final (`GT`) labels;
  and
- documentation needed to interpret the standardized records.

Unavailable original media or post-collection media repairs must be identified
in provenance rather than represented as original retrieved files.

## Conditions

Controlled access is limited to confidential peer-review inspection. Authorized
reviewers must not:

- redistribute, mirror, or publish the dataset or credentials;
- use the material for model training, commercial use, or unrelated research;
- identify, contact, profile, or harass source-platform users or depicted
  individuals;
- generate harmful content or circumvent safety systems; or
- disclose sensitive material outside the official review process.

Access does not transfer copyright or grant a general redistribution license
for source-platform media.

## Evidence limitations

Complete-dataset inspection can establish dataset scale, coverage, paired
media, labels, and record structure. It cannot recreate historical evidence
that was not retained, including:

- original retrieval logs, queries, and timestamps;
- unified per-rater `La` ballots or complete adjudication logs;
- original raw model responses, retries, refusals, and parser logs;
- all rendered prompts, decoding settings, and historical model revisions; or
- MIS judge outputs and human-validation records.

These limitations remain in force even when all 5,984 standardized records are
available for inspection.

## Post-review research access

Any later research release should use a separately documented application,
identity-verification, intended-use, and data-use-agreement process. Temporary
review access does not create a general public-access right.
