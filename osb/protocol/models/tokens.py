from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthToken:
    serial: Any


@dataclass
class TokenList:
    tokens: list[AuthToken]

    def take(self) -> AuthToken:
        if not self.tokens:
            raise ValueError("no authorisation tokens left")
        return self.tokens.pop()

    def __len__(self) -> int:
        return len(self.tokens)
