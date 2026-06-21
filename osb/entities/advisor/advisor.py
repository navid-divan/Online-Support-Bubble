from __future__ import annotations

from typing import Any

from osb.ports.transport import TransportPort
from osb.protocol.algorithms import find_offer, join_group, register_user
from osb.protocol.models.registration import UserCredentials


class Advisor:
    def __init__(self, transport: TransportPort, creds: UserCredentials) -> None:
        self.transport = transport
        self.creds = creds

    @staticmethod
    def register(transport: TransportPort, u: Any, upi: Any, attrs) -> "Advisor":
        return Advisor(transport, register_user(transport, u, upi, frozenset(attrs)))

    @property
    def public_key(self) -> Any:
        return self.creds.public_key

    def find_offer(self, shl: int) -> int | None:
        return find_offer(self.transport, self.creds, shl)

    def join(self, shl: int, idx: int):
        return join_group(self.transport, self.creds, shl, idx)
