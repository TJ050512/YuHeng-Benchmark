# Release subset and benchmark splits

This 900-record package is a reviewer-inspection subset of the 5,984-record benchmark. It is not a training split and should not be used to tune systems evaluated on YuHeng.

- Four domains contribute 225 records each.
- All nine `Lv × Lt` cells are represented inside every domain.
- `global_id` remains stable for controlled comparison with the full standardized benchmark.
- The full benchmark remains a separate controlled-access artifact.

If complete-benchmark inspection is requested and conference policy permits,
the authors are prepared to provide a time-limited, read-only reviewer link
through the official CMT or Program Chair channel. See the
[controlled-access procedure](../documentation/FULL_DATASET_ACCESS.md). No
public or placeholder credential is included in this repository.

No train/dev/test claim is made for these 900 records. Paper results should use the declared full-benchmark protocol and must not be recalculated on this public inspection subset unless clearly labeled as a separate subset experiment.
