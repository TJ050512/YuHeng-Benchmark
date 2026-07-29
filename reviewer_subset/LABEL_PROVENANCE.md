# Label provenance

## Retained

- `Lv`: standardized adjudicated visual label from the source export.
- `Lt`: standardized adjudicated textual label from the source export.
- `La`: standardized record-level association label and its reconstruction description.
- `GT`: derived by `max(Lv, Lt, La)`.

## Not retained

The available source folders do not contain one unified original per-rater ballot export for `La`. Consequently:

- this release does not publish individual `La` votes;
- per-label or per-domain `La` agreement cannot be recomputed from this artifact;
- the standardized reconstruction must not be described as if it were the missing raw ballot file;
- any claim about the original annotation process should be separated from what the released artifact can independently verify.

Every record exposes this limitation through `label_provenance.per_rater_La_ballots_retained=false`.
