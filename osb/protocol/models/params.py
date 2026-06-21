from __future__ import annotations

from dataclasses import dataclass

from osb.crypto import as_scheme, gs_scheme


@dataclass(frozen=True)
class PublicParams:
    aspp: as_scheme.ASParams
    tpk: gs_scheme.GSPublicKey
