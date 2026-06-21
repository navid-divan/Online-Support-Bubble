from __future__ import annotations

from typing import Any

from osb.ports.storage import StoragePort


class InMemoryStorage(StoragePort):
    def __init__(self) -> None:
        self._log: list[Any] = []
        self._ns: dict[str, dict[Any, Any]] = {}

    def append(self, entry: Any) -> int:
        self._log.append(entry)
        return len(self._log) - 1

    def read(self, hl: int) -> Any | None:
        if 0 <= hl < len(self._log):
            return self._log[hl]
        return None

    def overwrite(self, hl: int, entry: Any) -> bool:
        if 0 <= hl < len(self._log):
            self._log[hl] = entry
            return True
        return False

    def scan(self) -> list[tuple[int, Any]]:
        return list(enumerate(self._log))

    def put(self, ns: str, key: Any, value: Any) -> None:
        self._ns.setdefault(ns, {})[key] = value

    def get(self, ns: str, key: Any) -> Any | None:
        return self._ns.get(ns, {}).get(key)

    def contains(self, ns: str, key: Any) -> bool:
        return key in self._ns.get(ns, {})

    def items(self, ns: str) -> list[tuple[Any, Any]]:
        return list(self._ns.get(ns, {}).items())
