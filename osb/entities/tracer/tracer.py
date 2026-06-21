from __future__ import annotations

from typing import Any

from osb.crypto import gs_scheme
from osb.crypto.primitives import pairing as P
from osb.ports.storage import StoragePort

_CPKL = "cpkl"


class Tracer:
    def __init__(
        self, tpk: gs_scheme.GSPublicKey, tsk: gs_scheme.GSManagerKey, storage: StoragePort
    ) -> None:
        self._tpk = tpk
        self._tsk = tsk
        self._db = storage

    def assist_join(self, r: Any) -> tuple:
        return gs_scheme.join(self._tpk, self._tsk, r)

    def revocation_list(self) -> list:
        return [token for _, token in self._db.items(_CPKL)]

    def revoke(self, cpk: Any) -> None:
        self._db.put(_CPKL, P.g1_to_bytes(cpk), cpk)

    def trace(self, message: bytes, sig: gs_scheme.GSSignature):
        return gs_scheme.trace(self._tpk, self._tsk, message, sig)
