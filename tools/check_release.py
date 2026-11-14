#!/usr/bin/env python3
"""Self-contained integrity check for the YuHeng public subset."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

LABELS = ("Normal", "Suggestive", "Violation")
RANK = {label: index for index, label in enumerate(LABELS)}
DOMAINS = (
    "sexual_innuendo",
    "gender_bias",
    "socio_economic",
    "geographic_cultural_bias",
)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "release_root",
        nargs="?",
        type=Path,
        default=Path("public_subset"),
    )
    args = parser.parse_args()

    root = args.release_root.resolve()
    records = read_jsonl(root / "dataset.jsonl")
    errors: list[str] = []

    ids = [row.get("global_id") for row in records]
    if len(records) != 900:
        errors.append(f"expected 900 records, found {len(records)}")
    if len(set(ids)) != len(ids):
        errors.append("global_id values are not unique")

    domain_counts = Counter(row.get("domain") for row in records)
    expected_domains = Counter({domain: 225 for domain in DOMAINS})
    if domain_counts != expected_domains:
        errors.append(f"unexpected domain counts: {dict(domain_counts)}")

    covered_cells = {
        (row.get("domain"), row.get("Lv"), row.get("Lt")) for row in records
    }
    if len(covered_cells) != 36:
        errors.append(f"expected 36 domain × Lv × Lt cells, found {len(covered_cells)}")

    referenced_images: set[Path] = set()
    recorded_hashes: list[str] = []
    for line_number, row in enumerate(records, 1):
        for field in ("Lv", "Lt", "La", "GT"):
            if row.get(field) not in RANK:
                errors.append(
                    f"line {line_number}: invalid {field}={row.get(field)!r}"
                )
        if all(row.get(field) in RANK for field in ("Lv", "Lt", "La", "GT")):
            expected_gt = max(
                (row["Lv"], row["Lt"], row["La"]), key=RANK.__getitem__
            )
            if row["GT"] != expected_gt:
                errors.append(
                    f"line {line_number}: GT={row['GT']} but "
                    f"max(Lv,Lt,La)={expected_gt}"
                )

        relative = row.get("image_path")
        if not isinstance(relative, str):
            errors.append(f"line {line_number}: missing image_path")
            continue
        image = (root / relative).resolve()
        if not image.is_relative_to(root) or not image.is_file():
            errors.append(f"line {line_number}: missing or unsafe image {relative}")
            continue
        referenced_images.add(image)

        media = row.get("media") or {}
        actual_bytes = image.stat().st_size
        actual_hash = sha256(image)
        recorded_hashes.append(media.get("sha256"))
        if media.get("bytes") != actual_bytes:
            errors.append(f"line {line_number}: byte count mismatch for {relative}")
        if media.get("sha256") != actual_hash:
            errors.append(f"line {line_number}: SHA-256 mismatch for {relative}")

    actual_images = {
        path.resolve()
        for path in (root / "data").rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }
    if actual_images != referenced_images:
        errors.append(
            "image inventory differs from dataset references: "
            f"actual={len(actual_images)}, referenced={len(referenced_images)}"
        )
    if len(set(recorded_hashes)) != 900:
        errors.append("recorded media SHA-256 values are not 900 unique values")

    for domain in DOMAINS:
        expected = [row for row in records if row.get("domain") == domain]
        actual = read_json(root / "data" / domain / "dataset.json")
        if actual != expected:
            errors.append(f"{domain}: per-domain dataset does not match dataset.jsonl")

    manifest = read_json(root / "stats" / "selection_manifest.json")
    if manifest != records:
        errors.append("selection_manifest.json does not match dataset.jsonl")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "records": len(records),
        "unique_global_ids": len(set(ids)),
        "images": len(actual_images),
        "unique_media_hashes": len(set(recorded_hashes)),
        "domain_counts": dict(domain_counts),
        "covered_domain_lv_lt_cells": len(covered_cells),
        "GT": dict(Counter(row.get("GT") for row in records)),
        "La": dict(Counter(row.get("La") for row in records)),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
