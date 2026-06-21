from osb.crypto.as_scheme import (
    ASCredential,
    check,
    derive_pk,
    derive_sk,
    keygen,
    setup,
    sign,
    verify,
)
from osb.crypto.primitives import pairing as P


def test_keygen_is_valid_pair():
    pp = setup()
    kp = keygen(pp)
    assert P.g1_eq(P.g1_mul(pp.g, kp.sk), kp.pk)
    assert not P.g1_is_identity(kp.pk)


def test_correctness_derive_roundtrip():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk)
    dsk = derive_sk(pp, kp.sk, cred)
    assert dsk is not None
    assert check(pp, dpk, dsk)


def test_base_key_signs_and_verifies():
    pp = setup()
    kp = keygen(pp)
    assert verify(pp, kp.pk, b"support", sign(pp, kp.sk, b"support"))


def test_derived_key_signs_and_verifies():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk)
    dsk = derive_sk(pp, kp.sk, cred)
    assert verify(pp, dpk, b"support", sign(pp, dsk, b"support"))


def test_base_and_derived_keys_do_not_cross_verify():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk)
    dsk = derive_sk(pp, kp.sk, cred)
    assert not verify(pp, kp.pk, b"m", sign(pp, dsk, b"m"))
    assert not verify(pp, dpk, b"m", sign(pp, kp.sk, b"m"))


def test_each_derivation_is_fresh():
    pp = setup()
    kp = keygen(pp)
    dpk1, cred1 = derive_pk(pp, kp.pk)
    dpk2, cred2 = derive_pk(pp, kp.pk)
    assert not P.g1_eq(dpk1, dpk2)
    assert not P.g1_eq(cred1.E, cred2.E)
    assert cred1.mu != cred2.mu


def test_derived_pk_differs_from_base_and_is_well_formed():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk)
    assert not P.g1_eq(dpk, kp.pk)
    assert not P.g1_is_identity(dpk)
    dsk = derive_sk(pp, kp.sk, cred)
    assert P.g1_eq(P.g1_mul(pp.g, dsk), dpk)


def test_derived_pk_shape_matches_fresh_keygen():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk)
    dsk = derive_sk(pp, kp.sk, cred)
    fresh = keygen(pp)
    assert check(pp, dpk, dsk)
    assert check(pp, fresh.pk, fresh.sk)
    assert len(P.g1_to_bytes(dpk)) == len(P.g1_to_bytes(fresh.pk))


def test_derive_sk_rejects_credential_from_other_keypair():
    pp = setup()
    a = keygen(pp)
    b = keygen(pp)
    _, cred = derive_pk(pp, a.pk)
    assert derive_sk(pp, b.sk, cred) is None


def test_derive_sk_rejects_tampered_ephemeral():
    pp = setup()
    kp = keygen(pp)
    _, cred = derive_pk(pp, kp.pk)
    bad = ASCredential(E=P.g1_mul(pp.g, P.rand_scalar()), mu=cred.mu)
    assert derive_sk(pp, kp.sk, bad) is None


def test_derive_sk_rejects_tampered_mac():
    pp = setup()
    kp = keygen(pp)
    _, cred = derive_pk(pp, kp.pk)
    flipped = bytes([cred.mu[0] ^ 0x01]) + cred.mu[1:]
    assert derive_sk(pp, kp.sk, ASCredential(E=cred.E, mu=flipped)) is None


def test_check_is_false_on_none_secret():
    pp = setup()
    kp = keygen(pp)
    dpk, _ = derive_pk(pp, kp.pk)
    assert not check(pp, dpk, None)


def test_aux_binding_must_match():
    pp = setup()
    kp = keygen(pp)
    dpk, cred = derive_pk(pp, kp.pk, aux=b"context-a")
    assert derive_sk(pp, kp.sk, cred, aux=b"context-b") is None
    dsk = derive_sk(pp, kp.sk, cred, aux=b"context-a")
    assert check(pp, dpk, dsk)
