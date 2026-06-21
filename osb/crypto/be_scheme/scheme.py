from __future__ import annotations

import hashlib
from dataclasses import dataclass

from osb.crypto.primitives import aead
from osb.crypto.primitives import pairing as P

_KDF = b"osb/be/key"


@dataclass(frozen=True)
class BEPublicKey:
    n: int
    g1: P.G1Point
    W: P.G1Point
    kbase: P.GTElement


@dataclass(frozen=True)
class BEMemberKey:
    index: int
    b_i: P.G2Point
    D_i: P.G2Point


@dataclass(frozen=True)
class BECiphertext:
    c0: P.G1Point
    c1: P.G1Point
    blob: bytes


def setup(n: int) -> tuple[BEPublicKey, list[BEMemberKey]]:
    if n < 1:
        raise ValueError("n must be >= 1")
    g1, g2 = P.g1_generator(), P.g2_generator()
    alpha, gamma = P.rand_scalar(), P.rand_scalar()
    powers = [pow(alpha, k, P.ORDER) for k in range(2 * n + 1)]  # powers of alpha
    a = {k: P.g1_mul(g1, powers[k]) for k in range(1, n + 1)}
    bk = {k: P.g2_mul(g2, powers[k]) for k in [*range(1, n + 1), *range(n + 2, 2 * n + 1)]}
    W = P.g1_mul(g1, gamma)
    for k in range(1, n + 1):
        W = P.g1_add(W, a[k])
    pk = BEPublicKey(n=n, g1=g1, W=W, kbase=P.pair(a[n], bk[1]))
    members = []
    for i in range(1, n + 1):
        D = P.g2_mul(bk[i], gamma)
        for j in range(1, n + 1):
            if j != i:
                D = P.g2_add(D, bk[n + 1 - j + i])
        members.append(BEMemberKey(index=i, b_i=bk[i], D_i=D))
    return pk, members


def _sym_key(k: P.GTElement) -> bytes:
    return hashlib.sha256(_KDF + P.gt_to_bytes(k)).digest()


def encrypt(pk: BEPublicKey, message: bytes) -> BECiphertext:
    t = P.rand_scalar()
    k = P.gt_pow(pk.kbase, t)
    return BECiphertext(
        c0=P.g1_mul(pk.g1, t), c1=P.g1_mul(pk.W, t), blob=aead.seal(_sym_key(k), message)
    )


def decrypt(member: BEMemberKey, ct: BECiphertext) -> bytes | None:
    k = P.gt_mul(P.pair(ct.c1, member.b_i), P.gt_inv(P.pair(ct.c0, member.D_i)))
    return aead.unseal(_sym_key(k), ct.blob)
