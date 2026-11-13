"""Explicit provenance and missingness for every decision-critical input."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

T = TypeVar("T")


class EvidenceKind(StrEnum):
    OBSERVED = "OBSERVED"
    ESTIMATED = "ESTIMATED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Evidence(Generic[T]):
    value: T | None
    kind: EvidenceKind
    source: str | None = None
    caveat: str | None = None

    def __post_init__(self) -> None:
        if self.kind is EvidenceKind.UNKNOWN and self.value is not None:
            raise ValueError("UNKNOWN evidence must not contain an invented value")
        if self.kind is not EvidenceKind.UNKNOWN and self.value is None:
            raise ValueError("Known evidence requires a value")
