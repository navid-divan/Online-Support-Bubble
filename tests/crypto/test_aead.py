import secrets

from osb.crypto.primitives import aead


def test_roundtrip():
    key = secrets.token_bytes(32)
    msg = b"private support message"
    assert aead.unseal(key, aead.seal(key, msg)) == msg


def test_empty_message():
    key = secrets.token_bytes(32)
    assert aead.unseal(key, aead.seal(key, b"")) == b""


def test_wrong_key_fails():
    blob = aead.seal(secrets.token_bytes(32), b"secret")
    assert aead.unseal(secrets.token_bytes(32), blob) is None


def test_tamper_is_detected():
    key = secrets.token_bytes(32)
    blob = bytearray(aead.seal(key, b"hello world"))
    blob[-1] ^= 0x01
    assert aead.unseal(key, bytes(blob)) is None


def test_truncated_blob_fails():
    assert aead.unseal(secrets.token_bytes(32), b"short") is None


def test_ciphertext_is_randomized():
    key = secrets.token_bytes(32)
    assert aead.seal(key, b"x") != aead.seal(key, b"x")
