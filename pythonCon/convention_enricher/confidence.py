from __future__ import annotations

from typing import Literal


ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


def confidence_rank(level: ConfidenceLevel) -> int:
    return {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}[level]
