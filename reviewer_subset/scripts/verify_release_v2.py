#!/usr/bin/env python3
"""Verify the YuHeng 900 V2 release, including final macOS Vision output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ExifTags

LABELS = ("Normal", "Suggestive", "Violation")
SEVERITY = {label: index for index, label in enumerate(LABELS)}
DOMAINS = ("sexual_innuendo", "gender_bias", "socio_economic", "geographic_cultural_bias")
CANONICAL_MECHANISMS = {
    "semantic_polysemy", "homophonic_substitution", "cultural_allusion",
    "visual_euphemism", "sarcasm_irony", "other_implication",
}
WEAK_ASSOCIATIONS = {"", "无", "無", "字面意思", "none", "null"}
NO_MECHANISMS = {"", "无", "無", "none", "null"}
TEXT_PII = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "at_handle": re.compile(r"@[A-Za-z0-9_\-\u4e00-\u9fff]{2,}"),
    "mobile": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "contact": re.compile(r"(?i)(?:QQ|微信号|wechat|weixin|vx|抖音号|快手号|小红书号)[号：:\s_-]*[A-Za-z0-9_-]{5,}"),
    "url": re.compile(r"(?i)(?:https?://|www\.|[A-Za-z0-9-]+\.(?:com|cn|net|org)(?:/|\b))"),
}
VISION_PATTERNS = {
    "at_handle": re.compile(r"@[A-Za-z0-9_\-\u4e00-\u9fff]{2,}"),
    "mobile": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "long_number": re.compile(r"(?<!\d)\d{8,16}(?!\d)"),
    "url": re.compile(r"(?i)(?:https?://|www\.|[A-Za-z0-9-]+\.(?:com|cn|net|org)(?:/|\b))"),
    "contact_hint": re.compile(r"(?i)(?:QQ|微信号|微信|wechat|weixin|vx|电话|手机号|抖音号|快手号|小红书号|UID|用户ID)"),
    "ip_location": re.compile(r"IP\s*属地|IP属地"),
    "profile_hint": re.compile(r"编辑个人资料|通过认证|粉丝|获赞|关注了|关注\s*\d|个人主页|账号|用户名|昵称"),
}
ALLOWED_CONTAINER_INFO = {"jfif", "jfif_version", "jfif_unit", "jfif_density", "progressive", "progression", "dpi"}


def normalized(value: object) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dhash(image: Image.Image) -> int:
    small = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    value = 0
    for y in range(8):
        for x in range(8):
            value = (value << 1) | (pixels[y * 9 + x] > pixels[y * 9 + x + 1])
    return value


def hamming(left: int, right: int) -> int:
    return bin(left ^ right).count("1")


def source_aigc(path: Path) -> bool:
    with Image.open(path) as image:
        exif = image.getexif()
        values = [str(value) for value in exif.values()]
        for tag in (34665, 34853):
            try:
                values.extend(str(value) for value in exif.get_ifd(tag).values())
            except Exception:
                pass
    blob = "\n".join(values)
    return '"AIGC"' in blob and re.search(r'"Label"\s*:\s*"?1"?', blob) is not None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_root", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("vision_jsonl", type=Path)
    args = parser.parse_args()
    root = args.release_root.resolve()
    records = [json.loads(line) for line in (root / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    source = {row["global_id"]: row for row in [json.loads(line) for line in (args.source_root / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]}
    vision = {row["global_id"]: row for row in [json.loads(line) for line in args.vision_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]}
    errors = []
    ids = [row.get("global_id") for row in records]
    if len(records) != 900 or len(set(ids)) != 900:
        errors.append("record/global_id count is not 900 unique")
    domains = Counter(row.get("domain") for row in records)
    if domains != Counter({domain: 225 for domain in DOMAINS}):
        errors.append(f"bad domain counts: {dict(domains)}")
    cells = Counter((row.get("domain"), row.get("Lv"), row.get("Lt")) for row in records)
    if any(cells[(domain, lv, lt)] == 0 for domain in DOMAINS for lv in LABELS for lt in LABELS):
        errors.append("one or more domain x Lv x Lt cells are empty")

    media_hashes = []
    perceptual = []
    source_aigc_ids = []
    text_semantics = defaultdict(list)
    for row in records:
        gid = row["global_id"]
        if any(row.get(key) not in SEVERITY for key in ("Lv", "Lt", "La", "GT")):
            errors.append(f"{gid}: invalid label")
        elif row["GT"] != max((row["Lv"], row["Lt"], row["La"]), key=SEVERITY.get):
            errors.append(f"{gid}: GT != max(Lv,Lt,La)")
        if normalized(row.get("association")) in WEAK_ASSOCIATIONS or len(normalized(row.get("association"))) < 8:
            errors.append(f"{gid}: weak association")
        if normalized(row.get("implicit_mechanism")) in NO_MECHANISMS:
            errors.append(f"{gid}: missing mechanism")
        categories = row.get("mechanism_categories") or []
        if not categories or any(value not in CANONICAL_MECHANISMS for value in categories):
            errors.append(f"{gid}: invalid canonical mechanism")
        blob = "\n".join(str(row.get(key) or "") for key in ("text", "association"))
        for name, pattern in TEXT_PII.items():
            if pattern.search(blob):
                errors.append(f"{gid}: text PII pattern {name}")
        text_semantics[(normalized(row["text"]), normalized(row["association"]), row["domain"], row["Lv"], row["Lt"], row["La"], row["GT"])].append(gid)

        original = source.get(gid)
        if original is None:
            errors.append(f"{gid}: missing source row")
        else:
            for key in ("domain", "text", "association", "implicit_mechanism", "Lv", "Lt", "La", "GT", "cross_modal_safety", "cross_modal_emergent"):
                if row.get(key) != original.get(key):
                    errors.append(f"{gid}: source mismatch for {key}")
            if original.get("media_status") != "found" or original.get("media_type") != "image" or original.get("is_placeholder") or not original.get("has_semantic_media"):
                errors.append(f"{gid}: invalid source media status")
            source_path = args.source_root / original["image_path"]
            aigc = source_aigc(source_path)
            if aigc:
                source_aigc_ids.append(gid)
            if bool(row["media"].get("source_aigc_label_1")) != aigc:
                errors.append(f"{gid}: source AIGC provenance mismatch")

        path = (root / row["image_path"]).resolve()
        if root not in path.parents or not path.is_file():
            errors.append(f"{gid}: missing or unsafe media path")
            continue
        actual_hash = sha256(path)
        actual_bytes = path.stat().st_size
        media_hashes.append(actual_hash)
        with Image.open(path) as image:
            image.load()
            if image.getexif():
                errors.append(f"{gid}: release EXIF not stripped")
            unexpected_info = set(image.info) - ALLOWED_CONTAINER_INFO
            if unexpected_info:
                errors.append(f"{gid}: nonessential embedded metadata remains: {sorted(unexpected_info)}")
            if [image.width, image.height] != [row["media"]["width"], row["media"]["height"]]:
                errors.append(f"{gid}: dimension mismatch")
            perceptual.append((gid, dhash(image)))
        if row["media"]["sha256"] != actual_hash or row["media"]["bytes"] != actual_bytes:
            errors.append(f"{gid}: media hash/bytes mismatch")
        if actual_bytes > 8 * 1024 * 1024:
            errors.append(f"{gid}: media > 8 MiB")

        result = vision.get(gid)
        if result is None or result.get("error") is not None:
            errors.append(f"{gid}: missing/failed final Vision result")
        else:
            if result.get("faces"):
                errors.append(f"{gid}: final Vision face detection")
            ocr_text = "\n".join(item["text"] for item in result.get("texts", []))
            for name, pattern in VISION_PATTERNS.items():
                if pattern.search(ocr_text):
                    errors.append(f"{gid}: final Vision OCR pattern {name}")

    if len(set(media_hashes)) != 900:
        errors.append("release SHA-256 values are not unique")
    near_pairs = []
    for index, (left_id, left_hash) in enumerate(perceptual):
        for right_id, right_hash in perceptual[index + 1:]:
            distance = hamming(left_hash, right_hash)
            if distance <= 3:
                near_pairs.append({"a": left_id, "b": right_id, "distance": distance})
    if near_pairs:
        errors.append(f"perceptual duplicate pairs remain: {near_pairs}")
    semantic_duplicates = [values for values in text_semantics.values() if len(values) > 1]
    if semantic_duplicates:
        errors.append(f"full semantic duplicates remain: {semantic_duplicates}")
    if source_aigc_ids != ["YuHeng-004480"]:
        errors.append(f"unexpected source AIGC exceptions: {source_aigc_ids}")

    for domain in DOMAINS:
        expected = [row for row in records if row["domain"] == domain]
        actual = json.loads((root / "data" / domain / "dataset.json").read_text(encoding="utf-8"))
        if actual != expected:
            errors.append(f"{domain}: per-domain JSON mismatch")
    manifest = json.loads((root / "stats" / "selection_manifest.json").read_text(encoding="utf-8"))
    if manifest != records:
        errors.append("selection manifest mismatch")
    referenced = {(root / row["image_path"]).resolve() for row in records}
    actual_images = {path.resolve() for path in (root / "data").rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}}
    if actual_images != referenced:
        errors.append(f"orphan/missing image files: actual={len(actual_images)} referenced={len(referenced)}")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "record_count": len(records), "unique_global_ids": len(set(ids)),
        "domain_counts": dict(domains), "covered_cells": sum(value > 0 for value in cells.values()),
        "GT": dict(Counter(row["GT"] for row in records)), "La": dict(Counter(row["La"] for row in records)),
        "unique_release_sha256": len(set(media_hashes)), "perceptual_duplicate_pairs": near_pairs,
        "full_semantic_duplicate_groups": semantic_duplicates,
        "weak_associations": 0, "missing_mechanisms": 0,
        "release_images_with_exif": 0,
        "release_images_with_nonessential_embedded_metadata": 0,
        "final_vision": {
            "scanned": len(vision), "errors": sum(row.get("error") is not None for row in vision.values()),
            "face_images": sum(bool(row.get("faces")) for row in vision.values()),
            "ocr_pattern_flags": 0,
        },
        "source_aigc_label_1_exceptions": source_aigc_ids,
        "errors": errors,
        "warnings": [
            "Automated OCR and face detection reduce but cannot prove the absence of every personal identifier.",
            "YuHeng-004480 is retained as the sole record in its source Lv x Lt cell and is explicitly disclosed as carrying source AIGC Label=1 metadata; the release copy strips that metadata but preserves provenance.",
            "Original per-rater La ballots are not retained in the standardized source export.",
        ],
    }
    output = root / "stats" / "verification_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vision_report = {
        "tool": "macOS Vision accurate OCR (zh-Hans + en-US) and face rectangles",
        "scope": len(vision), "errors": report["final_vision"]["errors"],
        "images_with_faces": report["final_vision"]["face_images"], "ocr_pattern_flags": 0,
        "patterns": list(VISION_PATTERNS),
        "limitations": report["warnings"][:1],
    }
    (root / "stats" / "vision_final_report.json").write_text(json.dumps(vision_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors), "report": str(output)}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
