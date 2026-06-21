from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from osb.adapters.server import CentralServer
from osb.crypto.primitives import pairing as P
from osb.entities.advisor import Advisor
from osb.entities.subject import Subject
from osb.protocol.algorithms import open_channel
from osb.protocol.policy import Policy, validate

SAMPLE_ADVISORS = [
    ("walker", ["cancer_specialist", "experience_gt_10y"], "Dr. Martin Walker - oncologist (18 yrs)"),
    ("reyes", ["medical_doctor", "experience_gt_5y"], "Dr. Sofia Reyes - GP (9 yrs)"),
    ("bennett", ["legal_advisor"], "Sarah Bennett - solicitor"),
    ("marsh", ["legal_advisor"], "Diane Marsh - solicitor"),
    ("okonkwo", ["financial_specialist", "experience_gt_5y"], "James Okonkwo - financial adviser"),
    ("khan", ["mental_health_specialist", "experience_gt_10y"], "Dr. Aisha Khan - psychiatrist"),
    ("fielding", ["peer_survivor"], "Tom Fielding - peer survivor"),
]
SAMPLE_SUBJECT = ("emma", "Emma Clarke - recently diagnosed patient")


@dataclass
class BubbleState:
    bid: str
    owner: str
    policy: Policy
    handle: Any
    members: list = field(default_factory=list)  # (name, dpk, dsk)
    channel: Any = None
    closed: bool = False


class World:
    def __init__(self) -> None:
        self.server = CentralServer()
        self.users: dict[str, Any] = {}
        self.roles: dict[str, str] = {}
        self.profiles: dict[str, str] = {}
        self.advisor_names: dict[bytes, str] = {}
        self.bubbles: dict[str, BubbleState] = {}
        self._bcount = 0

    def seed(self) -> str:
        self.register_subject(SAMPLE_SUBJECT[0], SAMPLE_SUBJECT[1])
        for handle, attrs, display in SAMPLE_ADVISORS:
            self.register_advisor(handle, attrs, display)
        return f"seeded 1 subject and {len(SAMPLE_ADVISORS)} advisors"

    def register_subject(self, name: str, display: str | None = None) -> str:
        self._fresh(name)
        subject = Subject.register(self.server, name, f"{name}@osb")
        self.users[name] = subject
        self.roles[name] = "subject"
        self.profiles[name] = display or name
        return f"registered subject '{name}' ({len(subject.creds.tokens)} tokens)"

    def register_advisor(self, name: str, attrs: list[str], display: str | None = None) -> str:
        self._fresh(name)
        advisor = Advisor.register(self.server, name, f"{name}@osb", attrs)
        self.users[name] = advisor
        self.roles[name] = "advisor"
        self.profiles[name] = display or name
        self.advisor_names[P.g1_to_bytes(advisor.public_key)] = name
        return f"registered advisor '{name}' {sorted(frozenset(attrs))} ({len(advisor.creds.tokens)} tokens)"

    def list_advisors(self) -> str:
        lines = []
        for apk, att in self.server.list_advisors():
            b = P.g1_to_bytes(apk)
            handle = self.advisor_names.get(b, "?")
            tag = "available" if self.server.is_available(b) else "unavailable"
            lines.append(f"  {handle:<9} {self.profiles.get(handle, handle):<38} {sorted(att)} [{tag}]")
        return "advisors:\n" + ("\n".join(lines) if lines else "  (none)")

    def set_available(self, name: str, available: bool) -> str:
        advisor = self._advisor(name)
        self.server.set_availability(P.g1_to_bytes(advisor.public_key), available)
        return f"{name} is now {'available' if available else 'unavailable'}"

    def create_bubble(self, owner: str, policy_text: str) -> str:
        subject = self._subject(owner)
        policy = Policy.parse(policy_text)
        validate(policy)
        apkL = subject.get_advisors(policy)
        if apkL is None:
            raise ValueError("no set of available advisors satisfies that policy")
        handle = subject.start_bubble(apkL)
        if handle is None:
            raise ValueError("group creation failed (out of tokens?)")
        bid = f"b{self._bcount}"
        self._bcount += 1
        state = BubbleState(bid, owner, policy, handle, [(owner, handle.dspk, handle.dssk)])
        self._rebuild(state)
        self.bubbles[bid] = state
        invited = [self.advisor_names.get(P.g1_to_bytes(a), "?") for a in apkL]
        return f"created {bid} owned by '{owner}'; invited advisors: {invited}"

    def join(self, bid: str, advisor_name: str) -> str:
        state = self._bubble(bid)
        advisor = self._advisor(advisor_name)
        idx = advisor.find_offer(state.handle.shl)
        if idx is None:
            raise ValueError(f"'{advisor_name}' was not invited to {bid}")
        result = advisor.join(state.handle.shl, idx)
        if result is None:
            raise ValueError("join failed verification")
        state.members.append((advisor_name, result.dapk, result.dask))
        self._rebuild(state)
        return f"'{advisor_name}' joined {bid} as member #{len(state.members) - 1}"

    def send(self, bid: str, sender: str, text: str) -> str:
        state = self._bubble(bid)
        state.channel.send(self.server.pp, self._index(state, sender), text.encode())
        return f"{sender} -> {bid}: broadcast-encrypted ({len(text)} bytes)"

    def inbox(self, bid: str, reader: str) -> str:
        state = self._bubble(bid)
        msgs = state.channel.inbox(self.server.pp, self._index(state, reader))
        if not msgs:
            return f"{reader}'s inbox in {bid}: (empty)"
        lines = []
        for sidx, msg in msgs:
            who = state.members[sidx][0] if sidx < len(state.members) else f"#{sidx}"
            lines.append(f"  from {who}: {msg.decode(errors='replace')}")
        return f"{reader}'s inbox in {bid}:\n" + "\n".join(lines)

    def remove(self, bid: str, advisor_name: str) -> str:
        state = self._bubble(bid)
        member = self._member(state, advisor_name)
        self._subject(state.owner).remove_advisor(state.handle, member[1])
        state.members = [m for m in state.members if m[0] != advisor_name]
        self._rebuild(state)
        return f"removed '{advisor_name}' from {bid}"

    def replace(self, bid: str, advisor_name: str, policy_text: str | None = None) -> str:
        state = self._bubble(bid)
        member = self._member(state, advisor_name)
        policy = Policy.parse(policy_text) if policy_text else state.policy
        new_apkL = self._subject(state.owner).replace_advisor(state.handle, member[1], policy)
        state.members = [m for m in state.members if m[0] != advisor_name]
        self._rebuild(state)
        invited = [self.advisor_names.get(P.g1_to_bytes(a), "?") for a in new_apkL]
        return f"replaced '{advisor_name}' in {bid}; advisors now invited: {invited} (new ones must join)"

    def close(self, bid: str) -> str:
        state = self._bubble(bid)
        if not self._subject(state.owner).close(state.handle):
            raise ValueError("close failed")
        state.closed = True
        return f"closed {bid}"

    def trace(self, bid: str, member: str) -> str:
        state = self._bubble(bid)
        entry = self._member(state, member)
        cpk = self.server.osb_trace(entry[1])
        if cpk is None:
            raise ValueError(f"could not trace '{member}' (not on the ledger)")
        identity = self.server.judge(cpk)
        name = self.profiles.get(identity, identity)
        return f"traced '{member}': Registrar+Tracer reveal '{identity}' ({name}) - now revoked"

    def overview(self) -> str:
        lines = ["users:"]
        for n in self.users:
            lines.append(f"  {n:<9} {self.roles[n]:<8} {self.profiles.get(n, n)}")
        lines.append("bubbles:")
        if self.bubbles:
            for state in self.bubbles.values():
                names = ", ".join(m[0] for m in state.members)
                flag = " (closed)" if state.closed else ""
                lines.append(f"  {state.bid}: members=[{names}]{flag}")
        else:
            lines.append("  (none)")
        return "\n".join(lines)

    def _rebuild(self, state: BubbleState) -> None:
        members = [(dpk, dsk) for _, dpk, dsk in state.members]
        state.channel = open_channel(self.server.pp, members)

    def _fresh(self, name: str) -> None:
        if name in self.users:
            raise ValueError(f"user '{name}' already exists")

    def _subject(self, name: str) -> Subject:
        if self.roles.get(name) != "subject":
            raise ValueError(f"'{name}' is not a registered subject")
        return self.users[name]

    def _advisor(self, name: str) -> Advisor:
        if self.roles.get(name) != "advisor":
            raise ValueError(f"'{name}' is not a registered advisor")
        return self.users[name]

    def _bubble(self, bid: str) -> BubbleState:
        if bid not in self.bubbles:
            raise ValueError(f"unknown bubble '{bid}'")
        return self.bubbles[bid]

    def _index(self, state: BubbleState, name: str) -> int:
        for i, member in enumerate(state.members):
            if member[0] == name:
                return i
        raise ValueError(f"'{name}' is not a member of {state.bid}")

    def _member(self, state: BubbleState, name: str):
        return state.members[self._index(state, name)]
