import pytest

from osb.crypto.be_scheme import decrypt, encrypt, setup
from osb.crypto.primitives import pairing as P


@pytest.mark.parametrize("n", [1, 2, 3, 5])
def test_every_member_decrypts(n):
    pk, members = setup(n)
    ct = encrypt(pk, b"broadcast to the whole bubble")
    for m in members:
        assert decrypt(m, ct) == b"broadcast to the whole bubble"


def test_empty_message():
    pk, members = setup(3)
    ct = encrypt(pk, b"")
    assert decrypt(members[0], ct) == b""


def test_each_encrypt_is_fresh():
    pk, members = setup(2)
    c1, c2 = encrypt(pk, b"x"), encrypt(pk, b"x")
    assert not P.g1_eq(c1.c0, c2.c0)
    assert decrypt(members[0], c1) == b"x"
    assert decrypt(members[0], c2) == b"x"


def test_outsider_key_cannot_decrypt():
    pk, _ = setup(3)
    _, other_members = setup(3)
    ct = encrypt(pk, b"secret")
    assert decrypt(other_members[0], ct) is None


def test_setup_rejects_zero_members():
    with pytest.raises(ValueError):
        setup(0)
