import pytest

from osb.adapters.server import CentralServer
from osb.config import settings
from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import pairing as P
from osb.crypto.primitives import schnorr
from osb.protocol.algorithms import register_user
from osb.protocol.models.registration import RegistrationTuple


def test_subject_registration_end_to_end():
    server = CentralServer()
    creds = register_user(server, "alice", "alice@info")
    assert creds is not None
    assert len(creds.tokens) == settings.DEFAULT_SUBJECT_TOKENS
    assert server.ledger.is_permitted(P.g1_to_bytes(creds.public_key))
    sig = gs_scheme.sign(server.pp.tpk, creds.gs_key, b"msg")
    assert gs_scheme.verify(server.pp.tpk, [], b"msg", sig)


def test_advisor_registration_stores_attributes():
    server = CentralServer()
    att = frozenset({"cancer_specialist", "experience_gt_5y"})
    creds = register_user(server, "bob", "bob@info", att)
    assert creds is not None
    assert len(creds.tokens) == settings.DEFAULT_ADVISOR_TOKENS
    assert server.ledger.attributes_of(P.g1_to_bytes(creds.public_key)) == att


def test_two_registrations_are_distinct():
    server = CentralServer()
    a = register_user(server, "u1", "i1")
    b = register_user(server, "u2", "i2")
    assert not P.g1_eq(a.public_key, b.public_key)
    assert not P.g1_eq(a.cpk, b.cpk)


def test_registration_rejects_unknown_attribute():
    server = CentralServer()
    with pytest.raises(ValueError):
        register_user(server, "x", "i", frozenset({"bogus_attribute"}))


def test_registrar_rejects_forged_signature():
    server = CentralServer()
    pp = server.pp
    kp = as_scheme.keygen(pp.aspp)
    cpk, csk = server.tracer_join(P.rand_scalar())
    gsig = gs_scheme.sign(pp.tpk, csk, P.g1_to_bytes(kp.pk))
    good = as_scheme.sign(pp.aspp, kp.sk, gs_scheme.sig_to_bytes(gsig))
    assert server.registrar.onboard("good", "i", None, RegistrationTuple(kp.pk, gsig, good))
    bad = schnorr.SchnorrSig(c=good.c, s=(good.s + 1) % P.ORDER)
    assert not server.registrar.onboard("bad", "i", None, RegistrationTuple(kp.pk, gsig, bad))


def test_trace_and_judge_collaboration():
    server = CentralServer()
    creds = register_user(server, "carol", "carol@info")
    record = server.registrar.record_of("carol")
    out = server.tracer.trace(P.g1_to_bytes(creds.public_key), record.gsig)
    assert out is not None
    _, cpk = out
    assert P.g1_eq(cpk, creds.cpk)
    assert server.registrar.judge(cpk) == "carol"
