# Splits and evaluation protocol

YuHeng is an evaluation-only diagnostic benchmark. It has no training split.
The 5,984 benchmark items form the held-out evaluation set. The public subset uses deterministic selection and is reserved for evaluation.
Keep it out of model development and prompt tuning.

The 900-record public subset publishes its sampling seed,
stratification variables, selected IDs, cell quotas, and filtering statistics
in `public_subset/SELECTION.md`,
`public_subset/SPLITS.md`, and
`public_subset/stats/`. Seed `20260713` was used to construct this
subset and supports a deterministic rerun when the controlled 5,984-record
source and private Vision/candidate inputs are available; those inputs are not
all public. It is not an original data-retrieval seed. The original query-level
retrieval trail was not retained in reproducible form and cannot be reconstructed
from the release subset.
