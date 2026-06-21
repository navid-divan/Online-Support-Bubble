from __future__ import annotations

from dataclasses import dataclass

from osb.crypto.primitives import pairing as P

_CTX = b"osb/schnorr"


@dataclass(frozen=True)
class SchnorrSig:
    c: P.Scalar
    s: P.Scalar


def sign(sk: P.Scalar, message: bytes) -> SchnorrSig:
    pk = P.g1_mul(P.g1_generator(), sk)
    k = P.rand_scalar()
    R = P.g1_mul(P.g1_generator(), k)
    c = P.hash_to_scalar(_CTX, P.g1_to_bytes(R), P.g1_to_bytes(pk), message)
    s = (k + c * sk) % P.ORDER
    return SchnorrSig(c=c, s=s)


def verify(pk: P.G1Point, message: bytes, sig: SchnorrSig) -> bool:
    neg_c = (P.ORDER - sig.c) % P.ORDER
    R = P.g1_add(P.g1_mul(P.g1_generator(), sig.s), P.g1_mul(pk, neg_c))
    c = P.hash_to_scalar(_CTX, P.g1_to_bytes(R), P.g1_to_bytes(pk), message)
    return c == sig.c
