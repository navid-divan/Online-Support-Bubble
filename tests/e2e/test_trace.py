from osb.adapters.server import CentralServer
from osb.crypto.primitives import pairing as P
from osb.protocol.algorithms import (
    find_offer,
    get_advisors,
    join_group,
    register_user,
    start_group,
    verify_member_tuple,
)
from osb.protocol.policy import Policy

_POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def test_trace_subject_in_bubble():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    cpk = server.osb_trace(handle.dspk)
    assert cpk is not None
    assert P.g1_eq(cpk, subject.cpk)
    assert server.judge(cpk) == "subject"


def test_trace_advisor_in_bubble():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    cancer = register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    legal = register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    idx = find_offer(server, cancer, handle.shl)
    jr = join_group(server, cancer, handle.shl, idx)
    cpk = server.osb_trace(jr.dapk)
    assert cpk is not None
    assert P.g1_eq(cpk, cancer.cpk)
    assert server.judge(cpk) == "cancer"


def test_trace_revokes_the_member():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    grp = server.ledger_get(handle.shl)
    assert verify_member_tuple(server.pp, server.revocation_list(), grp.subject)
    server.osb_trace(handle.dspk)
    assert not verify_member_tuple(server.pp, server.revocation_list(), grp.subject)


def test_trace_unknown_key_returns_none():
    server = CentralServer()
    register_user(server, "subject", "s")
    fresh = P.g1_mul(P.g1_generator(), P.rand_scalar())
    assert server.osb_trace(fresh) is None
