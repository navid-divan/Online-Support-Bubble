from osb.adapters.server import CentralServer
from osb.crypto.primitives import pairing as P
from osb.protocol.algorithms import (
    close_group,
    find_offer,
    get_advisors,
    join_group,
    register_user,
    remove_advisor,
    replace_advisor,
    start_group,
    verify_member_tuple,
)
from osb.protocol.policy import Policy

_POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def _world():
    server = CentralServer()
    subject = register_user(server, "subject", "s@info")
    advisors = {
        "cancer": register_user(
            server, "cancer", "c", frozenset({"cancer_specialist", "experience_gt_5y"})
        ),
        "legal": register_user(server, "legal", "l", frozenset({"legal_advisor"})),
        "mh": register_user(server, "mh", "m", frozenset({"mental_health_specialist"})),
    }
    return server, subject, advisors


def test_get_advisors_covers_policy():
    server, _, _ = _world()
    apkL = get_advisors(server, _POLICY)
    assert apkL is not None
    assert len(apkL) == 2


def test_get_advisors_none_when_unsatisfiable():
    server, _, _ = _world()
    assert get_advisors(server, Policy.of({"financial_specialist"})) is None


def test_unavailable_advisor_is_skipped():
    server, _, advisors = _world()
    cancer2 = register_user(server, "cancer2", "c2", frozenset({"cancer_specialist"}))
    server.set_availability(P.g1_to_bytes(advisors["cancer"].public_key), False)
    apkL = get_advisors(server, Policy.of({"cancer_specialist"}))
    assert apkL is not None and len(apkL) == 1
    assert P.g1_to_bytes(apkL[0]) == P.g1_to_bytes(cancer2.public_key)


def test_form_bubble_and_advisors_join():
    server, subject, advisors = _world()
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    assert handle is not None and handle.shl == 0
    for name in ("cancer", "legal"):
        idx = find_offer(server, advisors[name], handle.shl)
        assert idx is not None
        jr = join_group(server, advisors[name], handle.shl, idx)
        assert jr is not None
        assert P.g1_eq(jr.dapk, server.ledger_get(handle.shl).offers[idx].dapk)


def test_outsider_advisor_has_no_offer():
    server, subject, advisors = _world()
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    assert find_offer(server, advisors["mh"], handle.shl) is None


def test_subject_tuple_verifies():
    server, subject, _ = _world()
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    grp = server.ledger_get(handle.shl)
    assert verify_member_tuple(server.pp, [], grp.subject)


def test_remove_advisor():
    server, subject, _ = _world()
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    dapk_star = server.ledger_get(handle.shl).offers[0].dapk
    new_apkL = remove_advisor(server, handle, dapk_star)
    assert len(new_apkL) == 1
    assert len(server.ledger_get(handle.shl).offers) == 1


def test_replace_advisor():
    server, subject, _ = _world()
    legal2 = register_user(server, "legal2", "l2", frozenset({"legal_advisor"}))
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    star = handle.apkL[1]
    dapk_star = server.ledger_get(handle.shl).offers[1].dapk
    new_apkL = replace_advisor(server, handle, dapk_star, _POLICY)
    assert len(new_apkL) == 2
    new_bytes = {P.g1_to_bytes(a) for a in new_apkL}
    assert P.g1_to_bytes(star) not in new_bytes
    assert P.g1_to_bytes(legal2.public_key) in new_bytes


def test_close_group():
    server, subject, _ = _world()
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    assert close_group(server, handle)
    assert server.ledger_get(handle.shl) is None
