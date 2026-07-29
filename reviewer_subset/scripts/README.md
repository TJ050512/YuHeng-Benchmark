# Reproduction scripts

The complete reproduction pipeline requires the private standardized
5,984-record source folder, Pillow, and macOS Vision. Install the Python image
dependency with:

```bash
python -m pip install -r reviewer_subset/scripts/requirements.txt
```

1. Run `prepare_candidates.py` on the standardized source.
2. Compile `vision_audit.swift` and scan the candidate JSONL.
3. Pass the candidate JSONL and Vision JSONL to `build_release_v2.py`.
4. Re-run `vision_audit.swift` on the materialized release.
5. Run `verify_release_v2.py` with the release, standardized source, and final Vision JSONL.

Example Vision compilation on macOS:

```bash
swiftc -O reviewer_subset/scripts/vision_audit.swift -o /tmp/yuheng_vision_audit
```

The selection seed is `20260713`. `YuHeng-004480` is a declared sole-cell AIGC-metadata exception and must not be silently removed or treated as an ordinary non-AIGC source record.
