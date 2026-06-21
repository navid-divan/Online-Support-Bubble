from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from osb.protocol.models.tokens import AuthToken, TokenList


class LedgerPort(ABC):
    @abstractmethod
    def register(self, pk: bytes, att: Any) -> TokenList | None: ...

    @abstractmethod
    def add(self, token: AuthToken, entry: Any) -> int | None: ...

    @abstractmethod
    def get(self, hl: int) -> Any | None: ...

    @abstractmethod
    def update(self, token: AuthToken, hl: int, entry: Any) -> bool: ...

    @abstractmethod
    def search(self, predicate: Callable[[Any], bool]) -> int | None: ...
