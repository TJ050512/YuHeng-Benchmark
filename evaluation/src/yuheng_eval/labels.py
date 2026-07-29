"""Canonical label definitions and source-label normalization."""

from __future__ import annotations

CANONICAL_LABELS = ("Normal", "Suggestive", "Violation")
SEVERITY = {"Normal": 0.0, "Suggestive": 0.5, "Violation": 1.0}

ALIASES = {
    "normal": "Normal",
    "理性讨论": "Normal",
    "正常": "Normal",
    "suggestive": "Suggestive",
    "teasing": "Suggestive",
    "soft porn": "Suggestive",
    "soft_porn": "Suggestive",
    "malicious": "Suggestive",
    "irritating": "Suggestive",
    "阴阳怪气": "Suggestive",
    "挑逗": "Suggestive",
    "软色情": "Suggestive",
    "violation": "Violation",
    "illegal": "Violation",
    "insulting": "Violation",
    "谩骂": "Violation",
    "违法": "Violation",
}


def normalize_label(value: object) -> str:
    """Map paper/source aliases to Normal, Suggestive, or Violation."""
    if not isinstance(value, str):
        raise ValueError(f"Label must be a string, got {type(value).__name__}")
    key = value.strip().lower()
    try:
        return ALIASES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown safety label: {value!r}") from exc


def severity(value: object) -> float:
    return SEVERITY[normalize_label(value)]
