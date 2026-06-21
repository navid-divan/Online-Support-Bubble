from osb.crypto.gs_scheme import (
    GSSignature,
    join,
    keygen,
    revoke,
    sign,
    trace,
    verify,
)
from osb.crypto.primitives import pairing as P


def _group(k):
    tpk, tsk = keygen()
    members = [join(tpk, tsk, f"user-{i}") for i in range(k)]
    return tpk, tsk, members


def _forged(tpk):
    return GSSignature(
        A_hat=P.g1_mul(tpk.g1, P.rand_scalar()),
        T1=P.g2_mul(tpk.g2, P.rand_scalar()),
        r=P.rand_scalar(),
        c=P.rand_scalar(),
        zx=P.rand_scalar(),
        zt=P.rand_scalar(),
    )


def test_sign_verifies_with_empty_revocation():
    tpk, tsk, [(cpk, csk)] = _group(1)
    assert verify(tpk, [], b"m", sign(tpk, csk, b"m"))


def test_unrevoked_when_other_member_revoked():
    tpk, tsk, ms = _group(2)
    (cpk0, csk0), (cpk1, _) = ms
    assert verify(tpk, [cpk1], b"hi", sign(tpk, csk0, b"hi"))


def test_revoked_signer_fails():
    tpk, tsk, [(cpk, csk)] = _group(1)
    sig = sign(tpk, csk, b"hi")
    assert verify(tpk, [], b"hi", sig)
    assert not verify(tpk, [cpk], b"hi", sig)


def test_wrong_message_fails():
    tpk, tsk, [(cpk, csk)] = _group(1)
    assert not verify(tpk, [], b"other", sign(tpk, csk, b"hi"))


def test_revoke_appends_and_is_idempotent():
    tpk, tsk, [(cpk, csk)] = _group(1)
    cpkL = revoke(tpk, tsk, cpk, [])
    assert any(P.g1_eq(cpk, rt) for rt in cpkL)
    assert revoke(tpk, tsk, cpk, cpkL) == cpkL


def test_signatures_are_randomized():
    tpk, tsk, [(cpk, csk)] = _group(1)
    s1, s2 = sign(tpk, csk, b"hi"), sign(tpk, csk, b"hi")
    assert not P.g1_eq(s1.A_hat, s2.A_hat)
    assert not P.g2_eq(s1.T1, s2.T1)


def test_trace_identifies_signer():
    tpk, tsk, ms = _group(3)
    cpk1, csk1 = ms[1]
    out = trace(tpk, tsk, b"trace me", sign(tpk, csk1, b"trace me"))
    assert out is not None
    u, cpk = out
    assert u == "user-1"
    assert P.g1_eq(cpk, cpk1)


def test_reject_forged_signature():
    tpk, tsk, _ = _group(1)
    assert not verify(tpk, [], b"m", _forged(tpk))


def test_trace_returns_none_on_forgery():
    tpk, tsk, _ = _group(2)
    assert trace(tpk, tsk, b"x", _forged(tpk)) is None


def test_selfless_anonymity_other_token_does_not_match():
    tpk, tsk, ms = _group(2)
    (cpk0, csk0), (cpk1, _) = ms
    sig = sign(tpk, csk0, b"anon")
    assert verify(tpk, [], b"anon", sig)
    assert verify(tpk, [cpk1], b"anon", sig)
