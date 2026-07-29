#!/usr/bin/env python3
"""Validate a YuHeng JSONL release before publication."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

LABELS = ("Normal", "Suggestive", "Violation")
RANK = {label: index for index, label in enumerate(LABELS)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--expected-count", type=int, default=5984)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: list[str] = []
    ids = [row.get("global_id") for row in rows]
    if len(rows) != args.expected_count:
        errors.append(f"expected {args.expected_count} rows, found {len(rows)}")
    if len(set(ids)) != len(ids):
        errors.append("global_id is not unique")
    for line_number, row in enumerate(rows, 1):
        for field in ("Lv", "Lt", "La", "GT"):
            if row.get(field) not in LABELS:
                errors.append(f"line {line_number}: invalid {field}={row.get(field)!r}")
        if all(row.get(field) in RANK for field in ("Lv", "Lt", "La", "GT")):
            expected = max((row["Lv"], row["Lt"], row["La"]), key=RANK.__getitem__)
            if row["GT"] != expected:
                errors.append(f"line {line_number}: GT={row['GT']} but max(Lv,Lt,La)={expected}")
        if args.media_root and row.get("image_path"):
            path = (args.media_root / row["image_path"]).resolve()
            if not path.is_relative_to(args.media_root.resolve()) or not path.is_file():
                errors.append(f"line {line_number}: missing/outside media {row['image_path']}")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "rows": len(rows),
        "errors": errors[:100],
        "error_count": len(errors),
        "domains": dict(Counter(row.get("domain") for row in rows)),
        "GT": dict(Counter(row.get("GT") for row in rows)),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
