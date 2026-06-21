from osb.adapters.storage import InMemoryStorage
from osb.entities.ledger import Ledger
from osb.protocol.models.tokens import AuthToken


def _ledger(subj=3, adv=5):
    return Ledger(InMemoryStorage(), subj, adv)


def test_register_requires_permitted_key():
    assert _ledger().register(b"pk", None) is None


def test_register_issues_subject_token_count():
    led = _ledger(subj=3, adv=5)
    led.permit(b"pk", None)
    assert len(led.register(b"pk", None)) == 3


def test_register_issues_advisor_token_count():
    led = _ledger(subj=3, adv=5)
    att = frozenset({"cancer_specialist"})
    led.permit(b"apk", att)
    assert len(led.register(b"apk", att)) == 5


def test_register_refuses_blacklisted():
    led = _ledger()
    led.permit(b"pk", None)
    led.blacklist(b"pk")
    assert led.register(b"pk", None) is None


def test_add_get_spends_token():
    led = _ledger()
    led.permit(b"pk", None)
    tok = led.register(b"pk", None).take()
    hl = led.add(tok, "entry-0")
    assert hl == 0
    assert led.get(hl) == "entry-0"


def test_token_cannot_be_reused():
    led = _ledger()
    led.permit(b"pk", None)
    tok = led.register(b"pk", None).take()
    assert led.add(tok, "x") == 0
    assert led.add(tok, "y") is None


def test_add_with_unknown_token_fails():
    assert _ledger().add(AuthToken(serial=b"bogus"), "x") is None


def test_update_requires_owning_token():
    led = _ledger()
    led.permit(b"pk", None)
    toks = led.register(b"pk", None)
    tok = toks.take()
    hl = led.add(tok, "old")
    assert led.update(tok, hl, "new")
    assert led.get(hl) == "new"
    assert not led.update(toks.take(), hl, "z")
    assert not led.update(AuthToken(serial=b"bogus"), hl, "z")


def test_search_returns_last_match():
    led = _ledger()
    led.permit(b"pk", None)
    toks = led.register(b"pk", None)
    led.add(toks.take(), "alpha")
    led.add(toks.take(), "beta")
    led.add(toks.take(), "alpha")
    assert led.search(lambda e: e == "alpha") == 2
    assert led.search(lambda e: e == "missing") is None
