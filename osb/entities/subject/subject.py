from __future__ import annotations

from typing import Any

from osb.ports.transport import TransportPort
from osb.protocol.algorithms import (
    close_group,
    get_advisors,
    register_user,
    remove_advisor,
    replace_advisor,
    start_group,
)
from osb.protocol.models.registration import UserCredentials
from osb.protocol.policy import Policy


class Subject:
    def __init__(self, transport: TransportPort, creds: UserCredentials) -> None:
        self.transport = transport
        self.creds = creds

    @staticmethod
    def register(transport: TransportPort, u: Any, upi: Any) -> "Subject":
        return Subject(transport, register_user(transport, u, upi))

    @property
    def public_key(self) -> Any:
        return self.creds.public_key

    def get_advisors(self, policy: Policy) -> list | None:
        return get_advisors(self.transport, policy)

    def start_bubble(self, apkL: list | None):
        return start_group(self.transport, self.creds, apkL)

    def close(self, handle) -> bool:
        return close_group(self.transport, handle)

    def remove_advisor(self, handle, dapk: Any) -> list:
        return remove_advisor(self.transport, handle, dapk)

    def replace_advisor(self, handle, dapk: Any, policy: Policy) -> list:
        return replace_advisor(self.transport, handle, dapk, policy)
