#!/usr/bin/env python3
"""Generate canonical image-row × text-column statistics from JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

LABELS = ("Normal", "Suggestive", "Violation")


def matrix(rows: list[dict]) -> dict[str, dict[str, int]]:
    counts = Counter((row["Lv"], row["Lt"]) for row in rows)
    return {lv: {lt: counts[(lv, lt)] for lt in LABELS} for lv in LABELS}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    domains = sorted({row["domain"] for row in rows})
    output = {
        "orientation": "rows=Lv(image), columns=Lt(text)",
        "labels": list(LABELS),
        "total": len(rows),
        "overall": matrix(rows),
        "per_domain": {
            domain: {"n": sum(row["domain"] == domain for row in rows), "matrix": matrix([row for row in rows if row["domain"] == domain])}
            for domain in domains
        },
        "marginals": {
            "Lv": dict(Counter(row["Lv"] for row in rows)),
            "Lt": dict(Counter(row["Lt"] for row in rows)),
            "La": dict(Counter(row["La"] for row in rows)),
            "GT": dict(Counter(row["GT"] for row in rows)),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
