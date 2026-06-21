from osb.adapters.server import CentralServer
from osb.crypto import be_scheme
from osb.protocol.algorithms import (
    find_offer,
    get_advisors,
    join_group,
    open_channel,
    open_message,
    register_user,
    start_group,
)
from osb.protocol.policy import Policy

_POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def _bubble_members(server):
    subject = register_user(server, "subject", "s")
    cancer = register_user(server, "cancer", "c", frozenset({"cancer_specialist"}))
    legal = register_user(server, "legal", "l", frozenset({"legal_advisor"}))
    handle = start_group(server, subject, get_advisors(server, _POLICY))
    members = [(handle.dspk, handle.dssk)]
    for creds in (cancer, legal):
        idx = find_offer(server, creds, handle.shl)
        jr = join_group(server, creds, handle.shl, idx)
        members.append((jr.dapk, jr.dask))
    return members


def test_every_member_reads_broadcast():
    server = CentralServer()
    members = _bubble_members(server)
    chan = open_channel(server.pp, members)
    chan.send(server.pp, 0, b"hello advisors")
    for reader in range(len(members)):
        inbox = chan.inbox(server.pp, reader)
        assert (0, b"hello advisors") in inbox


def test_messages_carry_authenticated_sender():
    server = CentralServer()
    members = _bubble_members(server)
    chan = open_channel(server.pp, members)
    chan.send(server.pp, 0, b"from subject")
    chan.send(server.pp, 2, b"from legal advisor")
    inbox = chan.inbox(server.pp, 1)
    assert (0, b"from subject") in inbox
    assert (2, b"from legal advisor") in inbox


def test_outsider_be_key_cannot_read():
    server = CentralServer()
    members = _bubble_members(server)
    chan = open_channel(server.pp, members)
    ct = chan.send(server.pp, 0, b"secret")
    _, outsiders = be_scheme.setup(len(members))
    assert open_message(server.pp, outsiders[0], chan.member_dpks, ct) is None


def test_forged_sender_signature_is_rejected():
    server = CentralServer()
    members = _bubble_members(server)
    chan = open_channel(server.pp, members)
    # advisor 1 claims to be the subject (index 0) using their own key
    payload = (0).to_bytes(4, "big") + (1).to_bytes(32, "big") + (1).to_bytes(32, "big") + b"spoof"
    ct = be_scheme.encrypt(chan.gpk, payload)
    assert open_message(server.pp, chan.member_keys[1], chan.member_dpks, ct) is None
