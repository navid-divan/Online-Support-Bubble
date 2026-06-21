from __future__ import annotations

import hashlib
import secrets
from typing import Any

from py_ecc.optimized_bls12_381 import (
    G1 as _G1,
    G2 as _G2,
    Z1 as _Z1,
    Z2 as _Z2,
    FQ12 as _FQ12,
    add as _add,
    curve_order as _ORDER,
    eq as _eq,
    is_inf as _is_inf,
    multiply as _multiply,
    neg as _neg,
    normalize as _normalize,
    pairing as _pairing,
)
from py_ecc.bls.hash_to_curve import hash_to_G2 as _hash_to_g2

from osb.config import params

Scalar = int
G1Point = Any
G2Point = Any
GTElement = Any

ORDER: int = _ORDER
G1_GEN: G1Point = _G1
G2_GEN: G2Point = _G2

assert ORDER == params.SCALAR_FIELD_ORDER, "pairing backend / params curve mismatch"

_FIELD_BYTES = (params.BASE_FIELD_MODULUS.bit_length() + 7) // 8


# scalars in z_r
def rand_scalar() -> Scalar:
    return 1 + secrets.randbelow(ORDER - 1)


def inv_scalar(x: Scalar) -> Scalar:
    return pow(x % ORDER, -1, ORDER)


def hash_to_scalar(*chunks: bytes) -> Scalar:
    h = hashlib.sha512()
    for c in chunks:
        h.update(len(c).to_bytes(8, "big"))
        h.update(c)
    return int.from_bytes(h.digest(), "big") % ORDER


# group g1
def g1_generator() -> G1Point:
    return _G1


def g1_identity() -> G1Point:
    return _Z1


def g1_mul(P: G1Point, n: Scalar) -> G1Point:
    n %= ORDER
    return _Z1 if n == 0 else _multiply(P, n)


def g1_add(P: G1Point, Q: G1Point) -> G1Point:
    return _add(P, Q)


def g1_neg(P: G1Point) -> G1Point:
    return _neg(P)


def g1_eq(P: G1Point, Q: G1Point) -> bool:
    return _eq(P, Q)


def g1_rand() -> G1Point:
    return _multiply(_G1, rand_scalar())


def g1_is_identity(P: G1Point) -> bool:
    return _is_inf(P)


# group g2
def g2_generator() -> G2Point:
    return _G2


def g2_identity() -> G2Point:
    return _Z2


def g2_mul(P: G2Point, n: Scalar) -> G2Point:
    n %= ORDER
    return _Z2 if n == 0 else _multiply(P, n)


def g2_add(P: G2Point, Q: G2Point) -> G2Point:
    return _add(P, Q)


def g2_neg(P: G2Point) -> G2Point:
    return _neg(P)


def g2_eq(P: G2Point, Q: G2Point) -> bool:
    return _eq(P, Q)


def g2_rand() -> G2Point:
    return _multiply(_G2, rand_scalar())


def g2_is_identity(P: G2Point) -> bool:
    return _is_inf(P)


# target group gt
def pair(P: G1Point, Q: G2Point) -> GTElement:
    return _pairing(Q, P)


def gt_one() -> GTElement:
    return _FQ12.one()


def gt_mul(a: GTElement, b: GTElement) -> GTElement:
    return a * b


def gt_pow(a: GTElement, n: Scalar) -> GTElement:
    return a ** (n % ORDER)


def gt_inv(a: GTElement) -> GTElement:
    return a ** (ORDER - 1)


def gt_eq(a: GTElement, b: GTElement) -> bool:
    return a == b


# serialization
def g1_to_bytes(P: G1Point) -> bytes:
    if _is_inf(P):
        return b"\x00"
    x, y = _normalize(P)
    return b"\x01" + x.n.to_bytes(_FIELD_BYTES, "big") + y.n.to_bytes(_FIELD_BYTES, "big")


def g2_to_bytes(P: G2Point) -> bytes:
    if _is_inf(P):
        return b"\x00"
    x, y = _normalize(P)
    out = b"\x01"
    for coeff in (*x.coeffs, *y.coeffs):
        out += int(coeff).to_bytes(_FIELD_BYTES, "big")
    return out


def gt_to_bytes(a: GTElement) -> bytes:
    return b"".join(int(c).to_bytes(_FIELD_BYTES, "big") for c in a.coeffs)


# hash to curve
_DST_G2 = b"OSB-BLS12381G2_XMD:SHA-256_SSWU_RO_"


def hash_to_g2(*chunks: bytes) -> G2Point:
    msg = b"".join(len(c).to_bytes(8, "big") + c for c in chunks)
    return _hash_to_g2(msg, _DST_G2, hashlib.sha256)
