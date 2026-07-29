# Splits and evaluation protocol

YuHeng is an evaluation-only diagnostic benchmark. It has no training split.
The 5,984 benchmark items form the held-out evaluation set. Any public peer-
review sample must be selected deterministically and must not be used for model
development or prompt tuning.

The 900-record reviewer-inspection subset publishes its sampling seed,
stratification variables, selected IDs, cell quotas, and filtering statistics
in `reviewer_subset/SELECTION.md`,
`reviewer_subset/SPLITS.md`, and
`reviewer_subset/stats/`. Seed `20260713` was used to construct this review
subset and supports a deterministic rerun when the controlled 5,984-record
source and private Vision/candidate inputs are available; those inputs are not
all public. It is not an original data-retrieval seed. The original query-level
retrieval trail was not retained in reproducible form and cannot be reconstructed
from the release subset.
