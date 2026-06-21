from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from osb.config.attributes import validate_all


@dataclass(frozen=True)
class Policy:
    clauses: tuple[frozenset[str], ...]  # cnf: and of or-clauses

    @staticmethod
    def of(*clauses: Iterable[str]) -> "Policy":
        return Policy(tuple(frozenset(c) for c in clauses))

    @staticmethod
    def parse(text: str) -> "Policy":
        clauses = []
        for part in text.split(";"):
            atts = [a.strip() for a in part.split(",") if a.strip()]
            if atts:
                clauses.append(frozenset(atts))
        return Policy(tuple(clauses))

    @property
    def size(self) -> int:
        return len(self.clauses)

    @property
    def attributes(self) -> frozenset[str]:
        out: set[str] = set()
        for clause in self.clauses:
            out |= clause
        return frozenset(out)

    def is_satisfied_by(self, attributes: Iterable[str]) -> bool:
        have = set(attributes)
        return all(len(clause & have) > 0 for clause in self.clauses)


def attr(attribute_sets: Iterable[Iterable[str]]) -> frozenset[str]:
    out: set[str] = set()
    for atts in attribute_sets:
        out |= set(atts)
    return frozenset(out)


def validate(policy: Policy) -> None:
    if policy.size == 0:
        raise ValueError("policy must have at least one clause")
    if any(len(clause) == 0 for clause in policy.clauses):
        raise ValueError("policy clauses must be non-empty")
    validate_all(policy.attributes)
