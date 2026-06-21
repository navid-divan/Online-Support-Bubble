from __future__ import annotations

from dataclasses import dataclass, field

from osb.crypto.primitives import pairing as P

_CTX = b"osb/gs/fs"
_BASE = b"osb/gs/base"


@dataclass(frozen=True)
class GSPublicKey:
    g1: P.G1Point
    g2: P.G2Point
    w: P.G2Point  # g2^gamma


@dataclass
class GSManagerKey:
    gamma: P.Scalar
    registry: list = field(default_factory=list)  # (u, cpk) pairs


@dataclass(frozen=True)
class GSSignKey:
    A: P.G1Point  # sdh credential
    x: P.Scalar


@dataclass(frozen=True)
class GSSignature:
    A_hat: P.G1Point
    T1: P.G2Point
    r: P.Scalar  # base nonce
    c: P.Scalar
    zx: P.Scalar
    zt: P.Scalar


def sig_to_bytes(sig: GSSignature) -> bytes:
    return b"".join(
        (
            P.g1_to_bytes(sig.A_hat),
            P.g2_to_bytes(sig.T1),
            sig.r.to_bytes(32, "big"),
            sig.c.to_bytes(32, "big"),
            sig.zx.to_bytes(32, "big"),
            sig.zt.to_bytes(32, "big"),
        )
    )


def keygen() -> tuple[GSPublicKey, GSManagerKey]:
    gamma = P.rand_scalar()
    tpk = GSPublicKey(g1=P.g1_generator(), g2=P.g2_generator(), w=P.g2_mul(P.g2_generator(), gamma))
    return tpk, GSManagerKey(gamma=gamma)


def join(tpk: GSPublicKey, tsk: GSManagerKey, u: object) -> tuple[P.G1Point, GSSignKey]:
    x = P.rand_scalar()
    while (tsk.gamma + x) % P.ORDER == 0:
        x = P.rand_scalar()
    A = P.g1_mul(tpk.g1, P.inv_scalar((tsk.gamma + x) % P.ORDER))
    tsk.registry.append((u, A))
    return A, GSSignKey(A=A, x=x)


def _base(tpk: GSPublicKey, message: bytes, r: P.Scalar) -> P.G2Point:
    return P.hash_to_g2(_BASE, P.g2_to_bytes(tpk.w), message, r.to_bytes(32, "big"))


def _challenge(tpk, message, A_hat, T1, r, Ra, Rb) -> P.Scalar:
    return P.hash_to_scalar(
        _CTX,
        P.g1_to_bytes(tpk.g1),
        P.g2_to_bytes(tpk.g2),
        P.g2_to_bytes(tpk.w),
        message,
        P.g1_to_bytes(A_hat),
        P.g2_to_bytes(T1),
        r.to_bytes(32, "big"),
        P.gt_to_bytes(Ra),
        P.g2_to_bytes(Rb),
    )


def sign(tpk: GSPublicKey, csk: GSSignKey, message: bytes) -> GSSignature:
    t = P.rand_scalar()
    A_hat = P.g1_mul(csk.A, t)
    r = P.rand_scalar()
    eta = _base(tpk, message, r)
    T1 = P.g2_mul(eta, t)
    P1 = P.pair(A_hat, tpk.g2)
    P2 = P.pair(tpk.g1, tpk.g2)
    bx, bt = P.rand_scalar(), P.rand_scalar()
    Ra = P.gt_mul(P.gt_pow(P1, bx), P.gt_pow(P2, (P.ORDER - bt) % P.ORDER))
    Rb = P.g2_mul(eta, bt)
    c = _challenge(tpk, message, A_hat, T1, r, Ra, Rb)
    return GSSignature(
        A_hat=A_hat, T1=T1, r=r, c=c, zx=(bx + c * csk.x) % P.ORDER, zt=(bt + c * t) % P.ORDER
    )


def _proof_ok(tpk: GSPublicKey, message: bytes, sig: GSSignature) -> tuple[bool, P.G2Point]:
    eta = _base(tpk, message, sig.r)
    P1 = P.pair(sig.A_hat, tpk.g2)
    P2 = P.pair(tpk.g1, tpk.g2)
    Pw = P.pair(sig.A_hat, tpk.w)
    Ra = P.gt_mul(
        P.gt_mul(P.gt_pow(P1, sig.zx), P.gt_pow(P2, (P.ORDER - sig.zt) % P.ORDER)),
        P.gt_pow(Pw, sig.c),
    )
    Rb = P.g2_add(P.g2_mul(eta, sig.zt), P.g2_mul(sig.T1, (P.ORDER - sig.c) % P.ORDER))
    return _challenge(tpk, message, sig.A_hat, sig.T1, sig.r, Ra, Rb) == sig.c, eta


def verify(tpk: GSPublicKey, cpkL: list, message: bytes, sig: GSSignature) -> bool:
    ok, eta = _proof_ok(tpk, message, sig)
    if not ok:
        return False
    rhs = P.pair(sig.A_hat, eta)
    return not any(P.gt_eq(P.pair(rt, sig.T1), rhs) for rt in cpkL)


def revoke(tpk: GSPublicKey, tsk: GSManagerKey, cpk: P.G1Point, cpkL: list) -> list:
    if any(P.g1_eq(cpk, rt) for rt in cpkL):
        return cpkL
    return cpkL + [cpk]


def trace(tpk: GSPublicKey, tsk: GSManagerKey, message: bytes, sig: GSSignature):
    ok, eta = _proof_ok(tpk, message, sig)
    if not ok:
        return None
    rhs = P.pair(sig.A_hat, eta)
    for u, cpk in tsk.registry:
        if P.gt_eq(P.pair(cpk, sig.T1), rhs):
            return u, cpk
    return None
