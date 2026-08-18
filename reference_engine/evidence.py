"""Evidence labelling for every field the reference engine asserts.

Nothing in this package may state a value without saying how it is known.
The five labels are ordered from strongest to weakest claim:

``MEASURED``
    Read directly from an instrument (MAME state, Yaba Sanshiro MCP dump,
    hardware register) or computed losslessly from such a reading.
``DECODED``
    Produced by a validated decoder over private source data, and recorded in
    a tracked copyright-safe artifact.
``INFERRED``
    A hypothesis consistent with current evidence that has not been falsified
    yet. It must carry a falsification test.
``ADAPTED``
    A deliberate platform decision made by this model. It is not a claim about
    what any original program does.
``UNRESOLVED``
    Named, required, and not known. It must carry the probe that would resolve
    it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MEASURED = "MEASURED"
DECODED = "DECODED"
INFERRED = "INFERRED"
ADAPTED = "ADAPTED"
UNRESOLVED = "UNRESOLVED"

EVIDENCE_LABELS = (MEASURED, DECODED, INFERRED, ADAPTED, UNRESOLVED)

#: Labels that must name what would disprove them.
_REQUIRE_FALSIFICATION = (INFERRED,)
#: Labels that must name the probe that would resolve or justify them.
_REQUIRE_PROBE = (UNRESOLVED,)


class EvidenceError(ValueError):
    """Raised when a claim is malformed for its evidence label."""


@dataclass(frozen=True)
class Claim:
    """One labelled field.

    ``value`` may be ``None`` for an ``UNRESOLVED`` claim; that is the point of
    the label. Any other label with a ``None`` value is a modelling bug.
    """

    label: str
    value: Any = None
    source: str = ""
    note: str = ""
    falsification: str = ""
    probe: str = ""

    def __post_init__(self) -> None:
        if self.label not in EVIDENCE_LABELS:
            raise EvidenceError(f"Unknown evidence label: {self.label!r}")
        if self.label in _REQUIRE_FALSIFICATION and not self.falsification:
            raise EvidenceError(f"{self.label} claim needs a falsification test: {self.source!r}")
        if self.label in _REQUIRE_PROBE and not self.probe:
            raise EvidenceError(f"{self.label} claim needs a resolving probe: {self.source!r}")
        if self.label != UNRESOLVED and self.value is None:
            raise EvidenceError(f"{self.label} claim has no value: {self.source!r}")
        if self.label in (MEASURED, DECODED) and not self.source:
            raise EvidenceError(f"{self.label} claim needs a source: {self.note!r}")

    def to_json(self) -> dict[str, Any]:
        """Deterministic, key-ordered serialisation."""
        record: dict[str, Any] = {"evidence": self.label, "value": self.value}
        for key in ("source", "note", "falsification", "probe"):
            text = getattr(self, key)
            if text:
                record[key] = text
        return record


def measured(value: Any, source: str, note: str = "") -> Claim:
    return Claim(MEASURED, value, source=source, note=note)


def decoded(value: Any, source: str, note: str = "") -> Claim:
    return Claim(DECODED, value, source=source, note=note)


def inferred(value: Any, falsification: str, source: str = "", note: str = "") -> Claim:
    return Claim(INFERRED, value, source=source, note=note, falsification=falsification)


def adapted(value: Any, note: str, source: str = "") -> Claim:
    return Claim(ADAPTED, value, source=source, note=note)


def unresolved(probe: str, note: str = "", source: str = "") -> Claim:
    return Claim(UNRESOLVED, None, source=source, note=note, probe=probe)


@dataclass
class ClaimSet:
    """An ordered, name-addressed collection of claims."""

    claims: dict[str, Claim] = field(default_factory=dict)

    def add(self, name: str, claim: Claim) -> "ClaimSet":
        if name in self.claims:
            raise EvidenceError(f"Duplicate claim name: {name!r}")
        self.claims[name] = claim
        return self

    def label_counts(self) -> dict[str, int]:
        counts = {label: 0 for label in EVIDENCE_LABELS}
        for claim in self.claims.values():
            counts[claim.label] += 1
        return counts

    def unresolved_names(self) -> list[str]:
        return sorted(n for n, c in self.claims.items() if c.label == UNRESOLVED)

    def to_json(self) -> dict[str, Any]:
        return {name: self.claims[name].to_json() for name in sorted(self.claims)}
