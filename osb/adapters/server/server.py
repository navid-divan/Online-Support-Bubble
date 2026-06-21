from __future__ import annotations

from typing import Any

from osb import profiling
from osb.adapters.storage.memory import InMemoryStorage
from osb.config import settings
from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import pairing as P
from osb.entities.ledger.ledger import Ledger
from osb.entities.registrar.registrar import Registrar
from osb.entities.tracer.tracer import Tracer
from osb.ports.storage import StoragePort
from osb.ports.transport import TransportPort
from osb.protocol.models.bubble import GroupEntry, MemberTuple
from osb.protocol.models.params import PublicParams
from osb.protocol.models.registration import RegistrationTuple
from osb.protocol.models.tokens import AuthToken, TokenList

_AVAIL = "avail"


def _tuple_for_dpk(entry: Any, target: bytes) -> MemberTuple | None:
    if isinstance(entry, MemberTuple) and P.g1_to_bytes(entry.dpk) == target:
        return entry
    if isinstance(entry, GroupEntry) and P.g1_to_bytes(entry.subject.dpk) == target:
        return entry.subject
    return None


class CentralServer(TransportPort):
    def __init__(self, storage: StoragePort | None = None) -> None:
        self._db = storage or InMemoryStorage()
        tpk, tsk = gs_scheme.keygen()
        self.pp = PublicParams(aspp=as_scheme.setup(), tpk=tpk)
        self.ledger = Ledger(
            self._db, settings.DEFAULT_SUBJECT_TOKENS, settings.DEFAULT_ADVISOR_TOKENS
        )
        self.tracer = Tracer(tpk, tsk, self._db)
        self.registrar = Registrar(self.pp, self._db, self.ledger)

    # registration endpoints
    def tracer_join(self, r: Any) -> tuple:
        return self.tracer.assist_join(r)

    def register(self, u: Any, upi: Any, att: Any, tup: RegistrationTuple) -> TokenList | None:
        if not self.registrar.onboard(u, upi, att, tup):
            return None
        apk = P.g1_to_bytes(tup.spk)
        if att:
            self._db.put(_AVAIL, apk, True)
        return self.ledger.register(apk, att)

    # ledger endpoints
    def ledger_add(self, token: AuthToken, entry: Any) -> int | None:
        return self.ledger.add(token, entry)

    def ledger_get(self, hl: int) -> Any | None:
        return self.ledger.get(hl)

    def ledger_update(self, token: AuthToken, hl: int, entry: Any) -> bool:
        return self.ledger.update(token, hl, entry)

    # advisor discovery
    def list_advisors(self) -> list:
        return self.ledger.advisor_directory()

    def is_available(self, apk: bytes) -> bool:
        return self._db.get(_AVAIL, apk) is not False

    def set_availability(self, apk: bytes, available: bool) -> None:
        self._db.put(_AVAIL, apk, available)

    # moderation
    def revocation_list(self) -> list:
        return self.tracer.revocation_list()

    def osb_trace(self, dpk: Any) -> Any | None:
        target = P.g1_to_bytes(dpk)
        hl = self.ledger.search(lambda e: _tuple_for_dpk(e, target) is not None)
        if hl is None:
            return None
        tup = _tuple_for_dpk(self.ledger.get(hl), target)
        msg = P.g1_to_bytes(tup.dpk)
        cpkL = self.tracer.revocation_list()
        if not gs_scheme.verify(self.pp.tpk, cpkL, msg, tup.gsig):
            return None
        if not as_scheme.verify(self.pp.aspp, tup.dpk, gs_scheme.sig_to_bytes(tup.gsig), tup.sig):
            return None
        traced = self.tracer.trace(msg, tup.gsig)
        if traced is None:
            return None
        _, cpk = traced
        self.tracer.revoke(cpk)
        return cpk

    def judge(self, cpk: Any) -> Any | None:
        return self.registrar.judge(cpk)


CentralServer.register = profiling.profile()(CentralServer.register)
CentralServer.tracer_join = profiling.profile()(CentralServer.tracer_join)
CentralServer.osb_trace = profiling.profile()(CentralServer.osb_trace)
CentralServer.judge = profiling.profile()(CentralServer.judge)
