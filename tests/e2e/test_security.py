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
from osb.protocol.models.bubble import MemberTuple
from osb.protocol.policy import Policy

_POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def _two_advisors(server):
    cancer = register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    legal = register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    return cancer, legal


def test_subject_keys_unlinkable_across_bubbles():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    _two_advisors(server)
    h1 = start_group(server, subject, get_advisors(server, _POLICY))
    h2 = start_group(server, subject, get_advisors(server, _POLICY))
    assert not P.g1_eq(h1.dspk, h2.dspk)
    assert not P.g1_eq(h1.dspk, subject.public_key)
    assert not P.g1_eq(h2.dspk, subject.public_key)


def test_advisor_keys_unlinkable_across_bubbles():
    server = CentralServer()
    s1 = register_user(server, "s1", "1")
    s2 = register_user(server, "s2", "2")
    cancer, _ = _two_advisors(server)
    h1 = start_group(server, s1, get_advisors(server, _POLICY))
    h2 = start_group(server, s2, get_advisors(server, _POLICY))
    j1 = join_group(server, cancer, h1.shl, find_offer(server, cancer, h1.shl))
    j2 = join_group(server, cancer, h2.shl, find_offer(server, cancer, h2.shl))
    assert not P.g1_eq(j1.dapk, j2.dapk)
    assert not P.g1_eq(j1.dapk, cancer.public_key)


def test_member_tuple_bound_to_its_derived_key():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    _two_advisors(server)
    h = start_group(server, subject, get_advisors(server, _POLICY))
    grp = server.ledger_get(h.shl)
    forged = MemberTuple(
        dpk=P.g1_mul(P.g1_generator(), P.rand_scalar()),
        gsig=grp.subject.gsig,
        sig=grp.subject.sig,
    )
    assert verify_member_tuple(server.pp, [], grp.subject)
    assert not verify_member_tuple(server.pp, [], forged)


def test_non_frameability_each_member_traces_to_itself():
    server = CentralServer()
    subject = register_user(server, "subject", "s")
    cancer = register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    legal = register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    h = start_group(server, subject, get_advisors(server, _POLICY))
    jc = join_group(server, cancer, h.shl, find_offer(server, cancer, h.shl))
    jl = join_group(server, legal, h.shl, find_offer(server, legal, h.shl))
    assert server.judge(server.osb_trace(h.dspk)) == "subject"
    assert server.judge(server.osb_trace(jc.dapk)) == "cancer"
    assert server.judge(server.osb_trace(jl.dapk)) == "legal"
