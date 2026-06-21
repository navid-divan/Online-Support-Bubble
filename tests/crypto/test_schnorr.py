from osb.crypto.primitives import pairing as P
from osb.crypto.primitives import schnorr


def _keypair():
    sk = P.rand_scalar()
    return sk, P.g1_mul(P.g1_generator(), sk)


def test_sign_verify_roundtrip():
    sk, pk = _keypair()
    assert schnorr.verify(pk, b"hello", schnorr.sign(sk, b"hello"))


def test_reject_wrong_message():
    sk, pk = _keypair()
    assert not schnorr.verify(pk, b"goodbye", schnorr.sign(sk, b"hello"))


def test_reject_wrong_key():
    sk, _ = _keypair()
    _, other_pk = _keypair()
    assert not schnorr.verify(other_pk, b"hello", schnorr.sign(sk, b"hello"))


def test_reject_tampered_signature():
    sk, pk = _keypair()
    sig = schnorr.sign(sk, b"hello")
    bad = schnorr.SchnorrSig(c=sig.c, s=(sig.s + 1) % P.ORDER)
    assert not schnorr.verify(pk, b"hello", bad)


def test_signatures_are_randomized():
    sk, pk = _keypair()
    s1 = schnorr.sign(sk, b"hello")
    s2 = schnorr.sign(sk, b"hello")
    assert (s1.c, s1.s) != (s2.c, s2.s)
    assert schnorr.verify(pk, b"hello", s1)
    assert schnorr.verify(pk, b"hello", s2)
