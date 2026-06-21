from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from osb import profiling
from osb.crypto import as_scheme, be_scheme
from osb.crypto.primitives import schnorr

_HEADER = 4 + 32 + 32


def seal(pp, gpk: Any, sender_index: int, sender_dsk: Any, message: bytes):
    sig = as_scheme.sign(pp.aspp, sender_dsk, message)
    payload = (
        sender_index.to_bytes(4, "big")
        + sig.c.to_bytes(32, "big")
        + sig.s.to_bytes(32, "big")
        + message
    )
    return be_scheme.encrypt(gpk, payload)


def open_message(pp, be_key: Any, member_dpks: list, ciphertext) -> tuple[int, bytes] | None:
    payload = be_scheme.decrypt(be_key, ciphertext)
    if payload is None or len(payload) < _HEADER:
        return None
    sender_index = int.from_bytes(payload[:4], "big")
    sig = schnorr.SchnorrSig(
        c=int.from_bytes(payload[4:36], "big"), s=int.from_bytes(payload[36:68], "big")
    )
    message = payload[_HEADER:]
    if not (0 <= sender_index < len(member_dpks)):
        return None
    if not as_scheme.verify(pp.aspp, member_dpks[sender_index], message, sig):
        return None
    return sender_index, message


@dataclass
class Channel:  # in-process broadcast channel for a bubble
    gpk: Any
    member_keys: list  # be secret key per member
    member_dpks: list  # derived public key per member
    member_dsks: list  # derived secret per member
    posted: list = field(default_factory=list)

    def send(self, pp, sender_index: int, message: bytes):
        ct = seal(pp, self.gpk, sender_index, self.member_dsks[sender_index], message)
        self.posted.append(ct)
        return ct

    def inbox(self, pp, reader_index: int) -> list:
        out = []
        for ct in self.posted:
            opened = open_message(pp, self.member_keys[reader_index], self.member_dpks, ct)
            if opened is not None:
                out.append(opened)
        return out


def open_channel(pp, members: list) -> Channel:
    gpk, keys = be_scheme.setup(len(members))
    return Channel(
        gpk=gpk,
        member_keys=keys,
        member_dpks=[dpk for dpk, _ in members],
        member_dsks=[dsk for _, dsk in members],
    )


seal = profiling.profile()(seal)
open_message = profiling.profile()(open_message)
