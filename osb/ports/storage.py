from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StoragePort(ABC):
    @abstractmethod
    def append(self, entry: Any) -> int: ...

    @abstractmethod
    def read(self, hl: int) -> Any | None: ...

    @abstractmethod
    def overwrite(self, hl: int, entry: Any) -> bool: ...

    @abstractmethod
    def scan(self) -> list[tuple[int, Any]]: ...

    @abstractmethod
    def put(self, ns: str, key: Any, value: Any) -> None: ...

    @abstractmethod
    def get(self, ns: str, key: Any) -> Any | None: ...

    @abstractmethod
    def contains(self, ns: str, key: Any) -> bool: ...

    @abstractmethod
    def items(self, ns: str) -> list[tuple[Any, Any]]: ...
