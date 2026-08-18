"""Deterministic semantic event traces.

A trace is the engine's primary output: an ordered list of what happened, in
source-semantic terms, with no rendering or hardware detail mixed in. Traces
are the unit an eventual MAME-versus-native parity harness would compare, so
their ordering must be total and reproducible.

Ordering is (frame, priority, kind, subject, detail). ``priority`` exists so
that events which logically precede others inside one frame -- a state entering
before the pose it selects, a collision before the damage it causes -- keep
that order without depending on insertion sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator

# Within-frame ordering. Lower runs first.
PRIORITY_INPUT = 10
PRIORITY_STATE_EXIT = 20
PRIORITY_STATE_ENTER = 30
PRIORITY_POSE = 40
PRIORITY_COLLISION = 50
PRIORITY_DAMAGE = 60
PRIORITY_AUDIO = 70
PRIORITY_RENDER = 80

KIND_PRIORITIES = {
    "input": PRIORITY_INPUT,
    "state_exit": PRIORITY_STATE_EXIT,
    "state_enter": PRIORITY_STATE_ENTER,
    "pose": PRIORITY_POSE,
    "collision": PRIORITY_COLLISION,
    "damage": PRIORITY_DAMAGE,
    "audio": PRIORITY_AUDIO,
    "render": PRIORITY_RENDER,
}


class TraceError(ValueError):
    """Raised when an event cannot be ordered deterministically."""


@dataclass(frozen=True)
class SemanticEvent:
    """One ordered semantic fact about one frame."""

    frame: int
    kind: str
    subject: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in KIND_PRIORITIES:
            raise TraceError("Unknown event kind %r" % (self.kind,))
        if self.frame < 0:
            raise TraceError("Event frame must not be negative")

    @property
    def priority(self) -> int:
        return KIND_PRIORITIES[self.kind]

    @property
    def sort_key(self) -> tuple[int, int, str, str, str]:
        return (
            self.frame,
            self.priority,
            self.kind,
            self.subject,
            _stable_detail(self.detail),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "frame": self.frame,
            "kind": self.kind,
            "subject": self.subject,
            "detail": {key: self.detail[key] for key in sorted(self.detail)},
        }


def _stable_detail(detail: dict[str, Any]) -> str:
    """A total, type-independent ordering key for a detail mapping."""
    return "|".join("%s=%r" % (key, detail[key]) for key in sorted(detail))


@dataclass
class EventTrace:
    """An append-then-sort trace with a total order."""

    events: list[SemanticEvent] = field(default_factory=list)

    def add(self, frame: int, kind: str, subject: str, **detail: Any) -> "EventTrace":
        self.events.append(SemanticEvent(frame=frame, kind=kind, subject=subject, detail=detail))
        return self

    def extend(self, events: Iterable[SemanticEvent]) -> "EventTrace":
        self.events.extend(events)
        return self

    def ordered(self) -> list[SemanticEvent]:
        return sorted(self.events, key=lambda event: event.sort_key)

    def __iter__(self) -> Iterator[SemanticEvent]:
        return iter(self.ordered())

    def __len__(self) -> int:
        return len(self.events)

    def of_kind(self, kind: str) -> list[SemanticEvent]:
        return [event for event in self.ordered() if event.kind == kind]

    def frames(self) -> list[int]:
        return sorted({event.frame for event in self.events})

    def kind_histogram(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.kind] = counts.get(event.kind, 0) + 1
        return dict(sorted(counts.items()))

    def is_totally_ordered(self) -> bool:
        """True when no two events share an identical sort key."""
        keys = [event.sort_key for event in self.events]
        return len(set(keys)) == len(keys)

    def to_json(self) -> list[dict[str, Any]]:
        return [event.to_json() for event in self.ordered()]
