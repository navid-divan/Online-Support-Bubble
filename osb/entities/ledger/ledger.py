from __future__ import annotations

import secrets
from collections.abc import Callable
from typing import Any

from osb.ports.ledger import LedgerPort
from osb.ports.storage import StoragePort
from osb.protocol.models.tokens import AuthToken, TokenList

_PKL = "pkl"
_BLACKL = "blackl"
_TOKENS = "tokens"
_UNSPENT = "unspent"


class Ledger(LedgerPort):
    def __init__(self, storage: StoragePort, subject_tokens: int, advisor_tokens: int) -> None:
        self._db = storage
        self._subject_tokens = subject_tokens
        self._advisor_tokens = advisor_tokens

    # shared public lists
    def permit(self, pk: bytes, att: Any, pk_point: Any = None) -> None:
        self._db.put(_PKL, pk, (att, pk_point))

    def is_permitted(self, pk: bytes) -> bool:
        return self._db.contains(_PKL, pk)

    def attributes_of(self, pk: bytes) -> Any:
        record = self._db.get(_PKL, pk)
        return record[0] if record else None

    def advisor_directory(self) -> list[tuple[Any, Any]]:
        out = []
        for _, (att, point) in self._db.items(_PKL):
            if att:
                out.append((point, att))
        return out

    def blacklist(self, pk: bytes) -> None:
        self._db.put(_BLACKL, pk, True)

    def is_blacklisted(self, pk: bytes) -> bool:
        return self._db.contains(_BLACKL, pk)

    # pl.register
    def register(self, pk: bytes, att: Any) -> TokenList | None:
        if not self._db.contains(_PKL, pk) or self._db.contains(_BLACKL, pk):
            return None
        count = self._advisor_tokens if att else self._subject_tokens
        tokens = []
        for _ in range(count):
            serial = secrets.token_bytes(16)
            self._db.put(_TOKENS, serial, _UNSPENT)
            tokens.append(AuthToken(serial=serial))
        return TokenList(tokens=tokens)

    # pl.add
    def add(self, token: AuthToken, entry: Any) -> int | None:
        if self._db.get(_TOKENS, token.serial) != _UNSPENT:
            return None
        hl = self._db.append(entry)
        self._db.put(_TOKENS, token.serial, ("owns", hl))
        return hl

    # pl.get
    def get(self, hl: int) -> Any | None:
        return self._db.read(hl)

    # pl.update
    def update(self, token: AuthToken, hl: int, entry: Any) -> bool:
        if self._db.get(_TOKENS, token.serial) != ("owns", hl):
            return False
        return self._db.overwrite(hl, entry)

    # pl.search
    def search(self, predicate: Callable[[Any], bool]) -> int | None:
        found = None
        for hl, entry in self._db.scan():
            if predicate(entry):
                found = hl
        return found
