#!/usr/bin/env python3
"""Build the strict pre-Vision candidate inventory for the YuHeng 900 V2 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from PIL import ExifTags, Image, ImageStat

LABELS = ("Normal", "Suggestive", "Violation")
DOMAINS = ("sexual_innuendo", "gender_bias", "socio_economic", "geographic_cultural_bias")
TEXT_PII = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "at_handle": re.compile(r"@[A-Za-z0-9_\-\u4e00-\u9fff]{2,}"),
    "mobile": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "contact_id": re.compile(r"(?i)(?:QQ|微信号|wechat|weixin|vx|抖音号|快手号|小红书号)[号：:\s_-]*[A-Za-z0-9_-]{5,}"),
    "url": re.compile(r"(?i)(?:https?://|www\.|[A-Za-z0-9-]+\.(?:com|cn|net|org)(?:/|\b))"),
}
WEAK_ASSOCIATIONS = {"", "无", "無", "字面意思", "none", "null"}
NO_MECHANISMS = {"", "无", "無", "none", "null"}


def normalized(value: object) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dhash(image: Image.Image, size: int = 8) -> str:
    small = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    value = 0
    for y in range(size):
        for x in range(size):
            value = (value << 1) | (pixels[y * (size + 1) + x] > pixels[y * (size + 1) + x + 1])
    return f"{value:016x}"


def exif_aigc(image: Image.Image) -> tuple[bool, bool, bool]:
    exif = image.getexif()
    if not exif:
        return False, False, False
    serialized = []
    device = False
    gps = False
    for key, value in exif.items():
        name = str(ExifTags.TAGS.get(key, key))
        serialized.append(f"{name}:{value}")
        if name in {"Make", "Model", "Software", "DateTime", "HostComputer", "MakerNote"}:
            device = True
    for name, tag in (("Exif", 34665), ("GPS", 34853)):
        try:
            nested = exif.get_ifd(tag)
        except Exception:
            nested = {}
        if name == "GPS" and nested:
            gps = True
        for key, value in nested.items():
            tag_name = str(ExifTags.TAGS.get(key, key))
            serialized.append(f"{name}.{tag_name}:{value}")
            if tag_name in {"Make", "Model", "Software", "DateTime", "DateTimeOriginal", "DateTimeDigitized", "HostComputer", "MakerNote", "UserComment"}:
                device = device or tag_name != "UserComment"
    blob = "\n".join(serialized)
    aigc = '"AIGC"' in blob and re.search(r'"Label"\s*:\s*"?1"?', blob) is not None
    return aigc, device, gps


def mechanism_categories(raw: object) -> list[str]:
    text = str(raw or "").lower()
    categories = []
    if any(token in text for token in ("一词多义", "polysemy", "语义双关")):
        categories.append("semantic_polysemy")
    if any(token in text for token in ("谐音", "homophon")):
        categories.append("homophonic_substitution")
    if any(token in text for token in ("文化", "典故", "借古喻今", "allusion")):
        categories.append("cultural_allusion")
    if any(token in text for token in ("表情包", "颜文字", "视觉", "以物喻人", "visual euphem")):
        categories.append("visual_euphemism")
    if any(token in text for token in ("反语", "反话", "反问", "irony", "sarcasm")):
        categories.append("sarcasm_irony")
    if not categories:
        categories.append("other_implication")
    return categories


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source_records = [json.loads(line) for line in (args.dataset_root / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    exclusions: Counter[str] = Counter()
    candidates = []
    for index, row in enumerate(source_records, 1):
        reasons = []
        if row.get("media_status") != "found": reasons.append("media_not_found")
        if row.get("media_type") != "image": reasons.append("non_image")
        if row.get("is_placeholder") or not row.get("has_semantic_media"): reasons.append("placeholder")
        if row.get("is_synthetic"): reasons.append("source_synthetic")
        blob = "\n".join(str(row.get(key) or "") for key in ("text", "association"))
        reasons.extend(f"text_{name}" for name, pattern in TEXT_PII.items() if pattern.search(blob))
        association_key = normalized(row.get("association"))
        mechanism_key = normalized(row.get("implicit_mechanism"))
        if association_key in WEAK_ASSOCIATIONS or len(association_key) < 8: reasons.append("weak_association")
        if mechanism_key in NO_MECHANISMS: reasons.append("no_mechanism")
        source_path = args.dataset_root / str(row.get("image_path") or "")
        if not source_path.is_file(): reasons.append("missing_file")
        if reasons:
            exclusions.update(set(reasons))
            continue
        try:
            with Image.open(source_path) as original:
                original.load()
                image = original.convert("RGB")
                width, height = image.size
                aigc, device_metadata, gps_metadata = exif_aigc(original)
        except Exception:
            exclusions["decode_failed"] += 1
            continue
        if min(width, height) < 128:
            exclusions["image_too_small"] += 1
            continue
        size = source_path.stat().st_size
        if size > 8 * 1024 * 1024:
            exclusions["image_over_8MiB"] += 1
            continue
        if aigc:
            exclusions["aigc_label_1"] += 1
            continue
        with Image.open(source_path) as original:
            rgb = original.convert("RGB")
            stat = ImageStat.Stat(rgb.resize((128, 128)))
            contrast = sum(stat.stddev) / 3
            visual_hash = dhash(rgb)
        candidate = dict(row)
        candidate["_source_path"] = str(source_path.resolve())
        candidate["_bytes"] = size
        candidate["_width"] = width
        candidate["_height"] = height
        candidate["_sha256"] = sha256(source_path)
        candidate["_dhash"] = visual_hash
        candidate["_has_exif"] = bool(Image.open(source_path).getexif())
        candidate["_device_metadata"] = device_metadata
        candidate["_gps_metadata"] = gps_metadata
        candidate["_association_length"] = len(association_key)
        candidate["_text_length"] = len(normalized(row.get("text")))
        candidate["_contrast"] = round(contrast, 4)
        candidate["canonical_mechanisms"] = mechanism_categories(row.get("implicit_mechanism"))
        candidates.append(candidate)
        if index % 500 == 0:
            print(f"processed {index}/{len(source_records)}", flush=True)

    with args.output.open("w", encoding="utf-8") as stream:
        for row in candidates:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    cells = Counter((row["domain"], row["Lv"], row["Lt"]) for row in candidates)
    report = {
        "source_records": len(source_records),
        "strict_pre_vision_candidates": len(candidates),
        "exclusions": dict(exclusions),
        "cells": [
            {"domain": domain, "Lv": lv, "Lt": lt, "count": cells[(domain, lv, lt)]}
            for domain in DOMAINS for lv in LABELS for lt in LABELS
        ],
    }
    report_path = args.output.with_suffix(".stats.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(candidates), "stats": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
