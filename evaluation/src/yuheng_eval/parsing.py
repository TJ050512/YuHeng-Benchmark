"""Strict, auditable parsing for model-produced structured outputs."""

from __future__ import annotations

import json
from typing import Any

from .labels import normalize_label

FIELD_ALIASES = {
    "level_of_word": ("level_of_word", "level of word", "textual_safety", "Lt"),
    "level_of_picture": ("level_of_picture", "level of picture", "visual_safety", "Lv"),
    "cross_modal_safety": ("cross_modal_safety", "cross modal safety", "cross_modal", "cross modal"),
    "final_risk_label": ("final_risk_label", "final risk label", "final_label", "GT"),
    "association": ("association",),
    "vague_methods": ("vague_methods", "vague methods"),
}

VAGUE_METHODS = {
    value.lower(): value
    for value in (
        "Implication",
        "Polysemy",
        "Deflection",
        "Ellipsis",
        "Meme Ambiguity",
        "Homophony",
        "Object Metaphor",
        "Internet Slang",
        "Kaomoji",
        "Irony",
        "None",
    )
}


def _json_objects(text: str) -> list[dict[str, Any]]:
    """Extract balanced JSON objects without accepting arbitrary Python syntax."""
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    return objects


def _get_field(payload: dict[str, Any], canonical_name: str) -> Any:
    for key in FIELD_ALIASES[canonical_name]:
        if key in payload:
            return payload[key]
    raise ValueError(f"Missing required field {canonical_name!r}")


def _normalize_yes_no(value: object) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str) and value.strip().lower() in {"yes", "no"}:
        return value.strip().title()
    raise ValueError(f"cross_modal_safety must be Yes/No, got {value!r}")


def _normalize_association(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("association must be a non-empty string")
    return value.strip()


def _normalize_vague_method(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("vague_methods must be a string")
    try:
        return VAGUE_METHODS[value.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unknown vague_methods value: {value!r}") from exc


def parse_model_output(text: str) -> dict[str, Any]:
    """Parse one model response and validate all six prompt-contract fields.

    The parser accepts a single JSON object or a JSON object embedded in a code
    fence/explanation. If multiple objects are present, the last complete object
    containing the required fields is selected. A parsing failure is explicit;
    callers must not silently coerce it into a correct prediction.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Model output is empty")
    candidates = _json_objects(text)
    if not candidates:
        raise ValueError("No valid JSON object found")
    errors: list[str] = []
    for payload in reversed(candidates):
        try:
            return {
                "level_of_word": normalize_label(_get_field(payload, "level_of_word")),
                "level_of_picture": normalize_label(_get_field(payload, "level_of_picture")),
                "cross_modal_safety": _normalize_yes_no(_get_field(payload, "cross_modal_safety")),
                "final_risk_label": normalize_label(_get_field(payload, "final_risk_label")),
                "association": _normalize_association(_get_field(payload, "association")),
                "vague_methods": _normalize_vague_method(_get_field(payload, "vague_methods")),
            }
        except ValueError as exc:
            errors.append(str(exc))
    raise ValueError("No JSON object satisfies the schema: " + "; ".join(errors))
