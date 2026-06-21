from __future__ import annotations

from collections.abc import Iterable

ATTRIBUTE_CATALOG: tuple[str, ...] = (
    "cancer_specialist",
    "financial_specialist",
    "mental_health_specialist",
    "legal_advisor",
    "medical_doctor",
    "experience_gt_5y",
    "experience_gt_10y",
    "peer_survivor",
)


def is_valid(attribute: str) -> bool:
    return attribute in ATTRIBUTE_CATALOG


def validate_all(attributes: Iterable[str]) -> None:
    unknown = sorted({a for a in attributes if a not in ATTRIBUTE_CATALOG})
    if unknown:
        raise ValueError(f"unknown attribute(s): {', '.join(unknown)}")
