from osb.adapters.server import CentralServer
from osb.entities.advisor import Advisor
from osb.entities.subject import Subject
from osb.protocol.policy import Policy

_POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def test_subject_and_advisors_form_and_join_bubble():
    server = CentralServer()
    alice = Subject.register(server, "alice", "a@osb")
    cancer = Advisor.register(server, "cancer", "c", {"cancer_specialist"})
    legal = Advisor.register(server, "legal", "l", {"legal_advisor"})
    handle = alice.start_bubble(alice.get_advisors(_POLICY))
    assert handle is not None
    for adv in (cancer, legal):
        idx = adv.find_offer(handle.shl)
        assert idx is not None
        assert adv.join(handle.shl, idx) is not None
    assert alice.close(handle)


def test_subject_get_advisors_none_when_unsatisfiable():
    server = CentralServer()
    alice = Subject.register(server, "alice", "a@osb")
    assert alice.get_advisors(Policy.of({"financial_specialist"})) is None


def test_advisor_not_invited_has_no_offer():
    server = CentralServer()
    alice = Subject.register(server, "alice", "a@osb")
    Advisor.register(server, "cancer", "c", {"cancer_specialist"})
    Advisor.register(server, "legal", "l", {"legal_advisor"})
    outsider = Advisor.register(server, "mh", "m", {"mental_health_specialist"})
    handle = alice.start_bubble(alice.get_advisors(_POLICY))
    assert outsider.find_offer(handle.shl) is None
