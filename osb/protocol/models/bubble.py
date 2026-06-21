from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemberTuple:  # (dpk, gsig, sig)
    dpk: Any
    gsig: Any
    sig: Any


@dataclass(frozen=True)
class AdvisorOffer:  # (dapk, cred) for a chosen advisor
    dapk: Any
    cred: Any


@dataclass
class GroupEntry:  # the grp posted at shl
    subject: MemberTuple
    offers: list = field(default_factory=list)


@dataclass
class BubbleHandle:  # subject's handle to their group
    tok: Any
    shl: int
    dspk: Any
    dssk: Any
    apkL: list = field(default_factory=list)


@dataclass(frozen=True)
class JoinResult:  # what an advisor keeps after joining
    ahl: int
    tok: Any
    dask: Any
    dapk: Any
