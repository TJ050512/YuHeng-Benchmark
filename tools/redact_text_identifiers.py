#!/usr/bin/env python3
"""Redact common direct identifiers in text fields; images still need manual review."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "<EMAIL>"),
    (re.compile(r"(?<![\w.])@[A-Za-z0-9_\-\u4e00-\u9fff]{2,}"), "@<USER>"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "<PHONE>"),
    (re.compile(r"(?i)(微信|vx|V信|QQ|qq号|微信号)[:： ]?[A-Za-z0-9_\-]{4,}"), "<CONTACT_ID>"),
]


def redact(value: object) -> object:
    if not isinstance(value, str):
        return value
    for pattern, replacement in PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("text", "association", "source_picture_address"):
            row[field] = redact(row.get(field))
        rows.append(row)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
