from __future__ import annotations

import hashlib
import hmac
import secrets

_NONCE_LEN = 16
_TAG_LEN = 32
_STREAM = b"osb/aead/stream"
_MAC = b"osb/aead/mac"


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(_STREAM + key + nonce + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:length])


def _tag(key: bytes, nonce: bytes, ct: bytes) -> bytes:
    mac_key = hashlib.sha256(_MAC + key).digest()
    return hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()


def seal(key: bytes, plaintext: bytes) -> bytes:
    nonce = secrets.token_bytes(_NONCE_LEN)
    ct = bytes(p ^ k for p, k in zip(plaintext, _keystream(key, nonce, len(plaintext))))
    return nonce + _tag(key, nonce, ct) + ct


def unseal(key: bytes, blob: bytes) -> bytes | None:
    if len(blob) < _NONCE_LEN + _TAG_LEN:
        return None
    nonce, tag, ct = blob[:_NONCE_LEN], blob[_NONCE_LEN:_NONCE_LEN + _TAG_LEN], blob[_NONCE_LEN + _TAG_LEN:]
    if not hmac.compare_digest(_tag(key, nonce, ct), tag):
        return None
    return bytes(c ^ k for c, k in zip(ct, _keystream(key, nonce, len(ct))))
