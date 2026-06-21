from __future__ import annotations

from osb.adapters.server.server import CentralServer
from osb.ports.storage import StoragePort
from osb.ports.transport import TransportPort


def connect(storage: StoragePort | None = None) -> TransportPort:
    return CentralServer(storage)
