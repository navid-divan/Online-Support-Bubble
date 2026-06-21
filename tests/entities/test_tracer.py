from osb.adapters.storage import InMemoryStorage
from osb.crypto import gs_scheme
from osb.crypto.primitives import pairing as P
from osb.entities.tracer import Tracer


def _tracer():
    tpk, tsk = gs_scheme.keygen()
    return tpk, Tracer(tpk, tsk, InMemoryStorage())


def test_assist_join_returns_usable_group_key():
    tpk, tr = _tracer()
    cpk, csk = tr.assist_join(P.rand_scalar())
    assert gs_scheme.verify(tpk, [], b"hello", gs_scheme.sign(tpk, csk, b"hello"))
    assert P.g1_eq(csk.A, cpk)


def test_revoke_then_signature_fails_verification():
    tpk, tr = _tracer()
    cpk, csk = tr.assist_join(P.rand_scalar())
    sig = gs_scheme.sign(tpk, csk, b"hi")
    tr.revoke(cpk)
    assert gs_scheme.verify(tpk, tr.revocation_list(), b"hi", sig) is False


def test_trace_finds_the_signer():
    tpk, tr = _tracer()
    cpk, csk = tr.assist_join("join-id")
    out = tr.trace(b"m", gs_scheme.sign(tpk, csk, b"m"))
    assert out is not None
    rid, traced = out
    assert rid == "join-id"
    assert P.g1_eq(traced, cpk)
