"""Core data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneSet:
    identifier: str
    name: str
    source: str
    genes: frozenset[str]


@dataclass(frozen=True)
class VariantRecord:
    gene: str
    variant: str = ""
    consequence: str = ""
    classification: str = ""
    disease: str = ""
    sample: str = ""

