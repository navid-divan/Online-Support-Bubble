from __future__ import annotations

from typing import Any

from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import pairing as P
from osb.entities.ledger.ledger import Ledger
from osb.ports.storage import StoragePort
from osb.protocol.models.params import PublicParams
from osb.protocol.models.registration import RegistrationTuple, UserRecord

_UL = "ul"
_CPKL = "cpkl"


class Registrar:
    def __init__(self, pp: PublicParams, storage: StoragePort, ledger: Ledger) -> None:
        self._pp = pp
        self._db = storage
        self._ledger = ledger

    def _revocation_list(self) -> list:
        return [token for _, token in self._db.items(_CPKL)]

    def onboard(self, u: Any, upi: Any, att: Any, tup: RegistrationTuple) -> bool:
        spk_bytes = P.g1_to_bytes(tup.spk)
        gsig_ok = gs_scheme.verify(self._pp.tpk, self._revocation_list(), spk_bytes, tup.gsig)
        sig_ok = as_scheme.verify(
            self._pp.aspp, tup.spk, gs_scheme.sig_to_bytes(tup.gsig), tup.sig
        )
        if not (gsig_ok and sig_ok):
            return False
        self._db.put(_UL, u, UserRecord(upi=upi, gsig=tup.gsig, spk=tup.spk))
        self._ledger.permit(spk_bytes, att, tup.spk)
        return True

    def record_of(self, u: Any) -> UserRecord | None:
        return self._db.get(_UL, u)

    def judge(self, cpk: Any) -> Any | None:
        for u, record in self._db.items(_UL):
            if gs_scheme.verify(self._pp.tpk, [cpk], P.g1_to_bytes(record.spk), record.gsig) is False:
                return u
        return None
