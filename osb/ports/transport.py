from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from osb.protocol.models.registration import RegistrationTuple
from osb.protocol.models.tokens import AuthToken, TokenList


class TransportPort(ABC):
    @abstractmethod
    def tracer_join(self, r: Any) -> tuple: ...

    @abstractmethod
    def register(self, u: Any, upi: Any, att: Any, tup: RegistrationTuple) -> TokenList | None: ...

    @abstractmethod
    def ledger_add(self, token: AuthToken, entry: Any) -> int | None: ...

    @abstractmethod
    def ledger_get(self, hl: int) -> Any | None: ...

    @abstractmethod
    def ledger_update(self, token: AuthToken, hl: int, entry: Any) -> bool: ...

    @abstractmethod
    def list_advisors(self) -> list: ...

    @abstractmethod
    def is_available(self, apk: bytes) -> bool: ...
