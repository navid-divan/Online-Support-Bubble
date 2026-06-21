from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from osb.crypto.primitives import pairing as P
from osb.crypto.primitives import schnorr

_BLIND = b"osb/as/blind"
_MAC_KEY = b"osb/as/mackey"
_MAC_TAG = b"osb/as/mactag"


@dataclass(frozen=True)
class ASParams:
    g: P.G1Point  # g1 generator


@dataclass(frozen=True)
class ASKeyPair:
    pk: P.G1Point
    sk: P.Scalar


@dataclass(frozen=True)
class ASCredential:
    E: P.G1Point  # ephemeral public key
    mu: bytes  # mac tag


def setup() -> ASParams:
    return ASParams(g=P.g1_generator())


def keygen(pp: ASParams) -> ASKeyPair:
    sk = P.rand_scalar()
    return ASKeyPair(pk=P.g1_mul(pp.g, sk), sk=sk)


def _blind(shared: bytes) -> P.Scalar:
    return P.hash_to_scalar(_BLIND, shared)


def _mac(shared: bytes, e_bytes: bytes, aux: bytes) -> bytes:
    key = hashlib.sha256(_MAC_KEY + shared).digest()
    return hmac.new(key, _MAC_TAG + e_bytes + aux, hashlib.sha256).digest()


def derive_pk(pp: ASParams, pk: P.G1Point, aux: bytes = b"") -> tuple[P.G1Point, ASCredential]:
    e = P.rand_scalar()
    E = P.g1_mul(pp.g, e)
    shared = P.g1_to_bytes(P.g1_mul(pk, e))
    dpk = P.g1_add(pk, P.g1_mul(pp.g, _blind(shared)))
    mu = _mac(shared, P.g1_to_bytes(E), aux)
    return dpk, ASCredential(E=E, mu=mu)


def derive_sk(
    pp: ASParams, sk: P.Scalar, cred: ASCredential, aux: bytes = b""
) -> P.Scalar | None:
    shared = P.g1_to_bytes(P.g1_mul(cred.E, sk))
    if not hmac.compare_digest(_mac(shared, P.g1_to_bytes(cred.E), aux), cred.mu):
        return None
    return (sk + _blind(shared)) % P.ORDER


def check(pp: ASParams, dpk: P.G1Point, dsk: P.Scalar | None) -> bool:
    if dsk is None:
        return False
    return P.g1_eq(P.g1_mul(pp.g, dsk), dpk)


def sign(pp: ASParams, ask: P.Scalar, message: bytes) -> schnorr.SchnorrSig:
    return schnorr.sign(ask, message)


def verify(pp: ASParams, apk: P.G1Point, message: bytes, sig: schnorr.SchnorrSig) -> bool:
    return schnorr.verify(apk, message, sig)
