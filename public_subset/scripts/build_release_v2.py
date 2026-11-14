#!/usr/bin/env python3
"""Select and materialize the privacy-first YuHeng 900 MMAsia 2026 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from PIL import ExifTags, Image, ImageOps, ImageStat

LABELS = ("Normal", "Suggestive", "Violation")
DOMAINS = ("sexual_innuendo", "gender_bias", "socio_economic", "geographic_cultural_bias")
SEVERITY = {label: index for index, label in enumerate(LABELS)}
EXCEPTION_ID = "YuHeng-004480"
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


def normalized(value: object) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).lower()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dhash_image(image: Image.Image, size: int = 8) -> int:
    small = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    value = 0
    for y in range(size):
        for x in range(size):
            value = (value << 1) | (pixels[y * (size + 1) + x] > pixels[y * (size + 1) + x + 1])
    return value


def hamming(left: int, right: int) -> int:
    return bin(left ^ right).count("1")


def source_aigc(image: Image.Image) -> bool:
    exif = image.getexif()
    if not exif:
        return False
    values = [str(value) for value in exif.values()]
    for tag in (34665, 34853):
        try:
            values.extend(str(value) for value in exif.get_ifd(tag).values())
        except Exception:
            pass
    blob = "\n".join(values)
    return '"AIGC"' in blob and re.search(r'"Label"\s*:\s*"?1"?', blob) is not None


def categories(raw: object) -> list[str]:
    text = str(raw or "").lower()
    output = []
    if any(token in text for token in ("一词多义", "polysemy", "语义双关")):
        output.append("semantic_polysemy")
    if any(token in text for token in ("谐音", "homophon")):
        output.append("homophonic_substitution")
    if any(token in text for token in ("文化", "典故", "借古喻今", "allusion")):
        output.append("cultural_allusion")
    if any(token in text for token in ("表情包", "颜文字", "视觉", "以物喻人", "visual euphem")):
        output.append("visual_euphemism")
    if any(token in text for token in ("反语", "反话", "反问", "irony", "sarcasm")):
        output.append("sarcasm_irony")
    if not output:
        output.append("other_implication")
    return output


def vision_flags(vision_row: dict) -> list[str]:
    text = "\n".join(item["text"] for item in vision_row.get("texts", []))
    return [name for name, pattern in VISION_PATTERNS.items() if pattern.search(text)]


def quality(row: dict, seed: int) -> float:
    jitter = random.Random(f"{seed}:{row['global_id']}").random() * 0.01
    score = 0.0
    score += min(math.log1p(row.get("_association_length", len(normalized(row.get("association"))))) / 2, 2.5)
    score += min(math.log1p(row.get("_text_length", len(normalized(row.get("text"))))) / 3, 2.0)
    score += min(float(row.get("_contrast", 20)) / 30, 1.0)
    score += 0.4 if len(row.get("canonical_mechanisms") or categories(row.get("implicit_mechanism"))) > 1 else 0.0
    aspect = max(row["_width"] / row["_height"], row["_height"] / row["_width"])
    if aspect > 6: score -= 0.8
    elif aspect > 4: score -= 0.35
    if min(row["_width"], row["_height"]) < 256: score -= 0.5
    return score + jitter


def allocate_quotas(candidates: list[dict]) -> dict[tuple[str, str, str], int]:
    available = Counter((row["domain"], row["Lv"], row["Lt"]) for row in candidates)
    quotas = {}
    for domain in DOMAINS:
        cells = [(domain, lv, lt) for lv in LABELS for lt in LABELS]
        for cell in cells:
            quotas[cell] = min(25, available[cell])
        deficit = 225 - sum(quotas[cell] for cell in cells)
        while deficit > 0:
            progressed = False
            for cell in sorted(cells, key=lambda value: (quotas[value], -available[value], value)):
                if quotas[cell] < available[cell]:
                    quotas[cell] += 1
                    deficit -= 1
                    progressed = True
                    if deficit == 0:
                        break
            if not progressed:
                raise RuntimeError(f"Not enough strict candidates for {domain}")
    return quotas


def select(candidates: list[dict], quotas: dict[tuple[str, str, str], int], seed: int) -> tuple[list[dict], dict, dict[tuple[str, str, str], int]]:
    by_cell: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in candidates:
        row["_quality"] = quality(row, seed)
        row["_text_hash"] = hashlib.sha256(normalized(row["text"]).encode()).hexdigest()
        row["_dhash_int"] = int(row["_dhash"], 16)
        by_cell[(row["domain"], row["Lv"], row["Lt"])].append(row)
    for rows in by_cell.values():
        rows.sort(key=lambda item: (-item["_quality"], item["global_id"]))

    selected = []
    used_sha = set()
    used_text = set()
    used_dhash: list[int] = []
    fallbacks = Counter()
    shortfalls = Counter()
    cell_order = sorted(quotas, key=lambda cell: (len(by_cell[cell]), quotas[cell], cell))
    for cell in cell_order:
        need = quotas[cell]
        pool = by_cell[cell]
        chosen = []
        # Four passes preserve exact media uniqueness first, then text uniqueness,
        # and only relax perceptual distance if a sparse cell makes that necessary.
        for require_text_unique, min_distance in ((True, 4), (False, 4), (True, 1), (False, 1)):
            for row in pool:
                if row in chosen or row["_sha256"] in used_sha:
                    continue
                if require_text_unique and row["_text_hash"] in used_text:
                    continue
                if any(hamming(row["_dhash_int"], value) < min_distance for value in used_dhash):
                    continue
                chosen.append(row)
                used_sha.add(row["_sha256"])
                used_text.add(row["_text_hash"])
                used_dhash.append(row["_dhash_int"])
                if len(chosen) == need:
                    break
            if len(chosen) == need:
                if not require_text_unique: fallbacks["text_duplicate_relaxation"] += 1
                if min_distance < 4: fallbacks["perceptual_distance_relaxation"] += 1
                break
        if len(chosen) != need:
            shortfalls[cell[0]] += need - len(chosen)
            fallbacks["quota_redistributed_after_perceptual_dedup"] += need - len(chosen)
        selected.extend(chosen)

    # Move any shortfall to another cell in the same domain instead of admitting
    # a perceptual duplicate. This preserves 225/domain and all non-empty cells.
    selected_ids = {row["global_id"] for row in selected}
    for domain, deficit in shortfalls.items():
        domain_pool = sorted(
            (row for row in candidates if row["domain"] == domain and row["global_id"] not in selected_ids),
            key=lambda row: (-row["_quality"], row["global_id"]),
        )
        for require_text_unique, min_distance in ((True, 4), (False, 4), (True, 1), (False, 1)):
            for row in domain_pool:
                if row["global_id"] in selected_ids or row["_sha256"] in used_sha:
                    continue
                if require_text_unique and row["_text_hash"] in used_text:
                    continue
                if any(hamming(row["_dhash_int"], value) < min_distance for value in used_dhash):
                    continue
                selected.append(row)
                selected_ids.add(row["global_id"])
                used_sha.add(row["_sha256"])
                used_text.add(row["_text_hash"])
                used_dhash.append(row["_dhash_int"])
                deficit -= 1
                if deficit == 0:
                    break
            if deficit == 0:
                if not require_text_unique: fallbacks["text_duplicate_relaxation"] += 1
                if min_distance < 4: fallbacks["perceptual_distance_relaxation"] += 1
                break
        if deficit:
            raise RuntimeError(f"Could not redistribute {deficit} records for {domain}")
    selected.sort(key=lambda row: row["global_id"])
    final_quotas = Counter((row["domain"], row["Lv"], row["Lt"]) for row in selected)
    return selected, dict(fallbacks), dict(final_quotas)


def write_image(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        transposed = ImageOps.exif_transpose(original)
        image = transposed.convert("RGB")
    image.info.clear()
    suffix = target.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.save(target, format="JPEG", quality=95, optimize=True, progressive=True)
    elif suffix == ".webp":
        image.save(target, format="WEBP", quality=95, method=6)
    else:
        image.save(target, format="PNG", optimize=True)
    if target.stat().st_size > 8 * 1024 * 1024:
        replacement = target.with_suffix(".jpg")
        image.save(replacement, format="JPEG", quality=94, optimize=True, progressive=True)
        target.unlink()
        target = replacement
    with Image.open(target) as check:
        exif_count = len(check.getexif())
        width, height = check.size
    return {
        "path": target,
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
        "width": width,
        "height": height,
        "exif_tags": exif_count,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_exception(source_root: Path) -> dict:
    source = next(
        json.loads(line) for line in (source_root / "dataset.jsonl").read_text(encoding="utf-8").splitlines()
        if json.loads(line)["global_id"] == EXCEPTION_ID
    )
    path = source_root / source["image_path"]
    with Image.open(path) as original:
        original.load()
        image = original.convert("RGB")
        width, height = image.size
        aigc = source_aigc(original)
        contrast = sum(ImageStat.Stat(image.resize((128, 128))).stddev) / 3
    source.update({
        "_source_path": str(path.resolve()), "_bytes": path.stat().st_size,
        "_width": width, "_height": height, "_sha256": sha256(path),
        "_dhash": f"{dhash_image(image):016x}", "_association_length": len(normalized(source["association"])),
        "_text_length": len(normalized(source["text"])), "_contrast": contrast,
        "canonical_mechanisms": categories(source.get("implicit_mechanism")),
        "_source_aigc_label_1": aigc, "_vision_face_count": 0, "_vision_flags": [],
        "_release_exception": "sole source record in socio_economic Lv=Violation Lt=Normal",
    })
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--vision", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260713)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    candidate_rows = [json.loads(line) for line in args.candidates.read_text(encoding="utf-8").splitlines() if line.strip()]
    vision = {row["global_id"]: row for row in [json.loads(line) for line in args.vision.read_text(encoding="utf-8").splitlines() if line.strip()]}
    strict = []
    vision_exclusions = Counter()
    for row in candidate_rows:
        result = vision.get(row["global_id"])
        if result is None or result.get("error") is not None:
            vision_exclusions["vision_missing_or_error"] += 1
            continue
        flags = vision_flags(result)
        if flags:
            vision_exclusions.update(f"vision_{flag}" for flag in flags)
            continue
        if result.get("faces"):
            vision_exclusions["vision_face_detected"] += 1
            continue
        row["_vision_flags"] = []
        row["_vision_face_count"] = 0
        row["_source_aigc_label_1"] = False
        strict.append(row)
    strict.append(build_exception(args.source_root))
    quotas = allocate_quotas(strict)
    selected, fallbacks, quotas = select(strict, quotas, args.seed)
    if len(selected) != 900:
        raise RuntimeError(f"selected {len(selected)} records")

    args.output.mkdir(parents=True)
    public = []
    for index, row in enumerate(selected, 1):
        extension = Path(row["_source_path"]).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            extension = ".png"
        relative = Path("data") / row["domain"] / "images" / f"{row['global_id']}{extension}"
        media = write_image(Path(row["_source_path"]), args.output / relative)
        relative = media["path"].relative_to(args.output)
        record = {
            "global_id": row["global_id"], "domain": row["domain"],
            "domain_zh": row.get("domain_zh"), "domain_en": row.get("domain_en"),
            "text": row["text"], "image_path": relative.as_posix(),
            "association": row["association"],
            "implicit_mechanism": row.get("implicit_mechanism"),
            "mechanism_categories": row.get("canonical_mechanisms") or categories(row.get("implicit_mechanism")),
            "Lv": row["Lv"], "Lt": row["Lt"], "La": row["La"], "GT": row["GT"],
            "cross_modal_safety": row.get("cross_modal_safety"),
            "cross_modal_emergent": row.get("cross_modal_emergent"),
            "label_provenance": {
                "Lv": "source adjudicated export", "Lt": "source adjudicated export",
                "La": row.get("La_derivation", "deterministic standardized reconstruction"),
                "GT": "derived as max(Lv,Lt,La)",
                "per_rater_La_ballots_retained": False,
            },
            "media": {
                "sha256": media["sha256"], "bytes": media["bytes"],
                "width": media["width"], "height": media["height"],
                "metadata_stripped": media["exif_tags"] == 0,
                "vision_privacy_flags": row.get("_vision_flags", []),
                "vision_face_count": row.get("_vision_face_count", 0),
                "source_aigc_label_1": bool(row.get("_source_aigc_label_1")),
            },
            "selection": {
                "seed": args.seed, "quality_score": round(row["_quality"], 6),
                "privacy_first": True,
                "exception": row.get("_release_exception"),
            },
        }
        if record["GT"] != max((record["Lv"], record["Lt"], record["La"]), key=SEVERITY.get):
            raise RuntimeError(f"bad GT: {record['global_id']}")
        public.append(record)
        if index % 100 == 0:
            print(f"materialized {index}/900", flush=True)

    with (args.output / "dataset.jsonl").open("w", encoding="utf-8") as stream:
        for row in public:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    for domain in DOMAINS:
        write_json(args.output / "data" / domain / "dataset.json", [row for row in public if row["domain"] == domain])
    write_json(args.output / "stats" / "selection_manifest.json", public)
    available = Counter((row["domain"], row["Lv"], row["Lt"]) for row in strict)
    selected_counts = Counter((row["domain"], row["Lv"], row["Lt"]) for row in public)
    stats = {
        "dataset": "YuHeng 900 MMAsia 2026 Public Subset", "seed": args.seed,
        "selection_count": len(public), "per_domain": dict(Counter(row["domain"] for row in public)),
        "GT": dict(Counter(row["GT"] for row in public)), "La": dict(Counter(row["La"] for row in public)),
        "strict_candidate_count_including_exception": len(strict),
        "vision_exclusions": dict(vision_exclusions), "selection_fallbacks": fallbacks,
        "quota_table": [
            {"domain": domain, "Lv": lv, "Lt": lt, "strict_available": available[(domain, lv, lt)],
             "quota": quotas[(domain, lv, lt)], "selected_count": selected_counts[(domain, lv, lt)]}
            for domain in DOMAINS for lv in LABELS for lt in LABELS
        ],
        "privacy": {
            "vision_scanned_candidates": len(vision), "selected_vision_privacy_flags": 0,
            "selected_vision_faces": 0, "source_aigc_label_1_exceptions": [row["global_id"] for row in public if row["media"]["source_aigc_label_1"]],
            "all_release_exif_stripped": all(row["media"]["metadata_stripped"] for row in public),
        },
        "duplicates": {
            "unique_release_sha256": len({row["media"]["sha256"] for row in public}),
            "unique_normalized_texts": len({normalized(row["text"]) for row in public}),
        },
        "media": {
            "logical_bytes": sum(row["media"]["bytes"] for row in public),
            "max_file_bytes": max(row["media"]["bytes"] for row in public),
            "all_files_below_8MiB": all(row["media"]["bytes"] <= 8 * 1024 * 1024 for row in public),
        },
    }
    write_json(args.output / "stats" / "selection_stats.json", stats)
    print(json.dumps({"output": str(args.output), "selected": len(public), "stats": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
