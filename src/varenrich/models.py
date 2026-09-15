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
    chromosome: str = ""
    position: int | None = None
    reference: str = ""
    alternate: str = ""
    consequence: str = ""
    classification: str = ""
    disease: str = ""
    sample: str = ""
    quality: float | None = None
    filter_status: str = ""
    allele_frequency: float | None = None
    zygosity: str = ""
