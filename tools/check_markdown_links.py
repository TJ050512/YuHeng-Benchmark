#!/usr/bin/env python3
"""Check that local Markdown link targets exist."""

from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "#")


def main() -> None:
    root = Path(".").resolve()
    markdown_files = sorted(root.rglob("*.md"))
    checked = 0
    missing: list[str] = []

    for document in markdown_files:
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(REMOTE_PREFIXES):
                continue
            path_text = target.split("#", 1)[0]
            if not path_text:
                continue
            checked += 1
            resolved = (document.parent / path_text).resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                missing.append(
                    f"{document.relative_to(root)} -> {raw_target}"
                )

    print(
        f"markdown_files={len(markdown_files)} "
        f"local_links={checked} missing={len(missing)}"
    )
    for item in missing:
        print(item)
    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()
