from __future__ import annotations

from typing import Any

from osb import profiling
from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import pairing as P
from osb.ports.transport import TransportPort
from osb.protocol.models.bubble import (
    AdvisorOffer,
    BubbleHandle,
    GroupEntry,
    JoinResult,
    MemberTuple,
)
from osb.protocol.models.registration import UserCredentials
from osb.protocol.policy import Policy


def _member_tuple(pp, csk, dpk: Any, dsk: Any) -> MemberTuple:
    gsig = gs_scheme.sign(pp.tpk, csk, P.g1_to_bytes(dpk))
    sig = as_scheme.sign(pp.aspp, dsk, gs_scheme.sig_to_bytes(gsig))
    return MemberTuple(dpk=dpk, gsig=gsig, sig=sig)


def verify_member_tuple(pp, cpkL: list, tup: MemberTuple) -> bool:
    return gs_scheme.verify(
        pp.tpk, cpkL, P.g1_to_bytes(tup.dpk), tup.gsig
    ) and as_scheme.verify(pp.aspp, tup.dpk, gs_scheme.sig_to_bytes(tup.gsig), tup.sig)


def get_advisors(transport: TransportPort, policy: Policy) -> list | None:
    available = [
        (apk, frozenset(att))
        for apk, att in transport.list_advisors()
        if transport.is_available(P.g1_to_bytes(apk))
    ]
    chosen: list = []
    chosen_bytes: set = set()
    chosen_attrs: set = set()
    for clause in policy.clauses:
        if chosen_attrs & clause:
            continue
        pick = None
        for apk, att in available:
            b = P.g1_to_bytes(apk)
            if b not in chosen_bytes and (att & clause):
                pick = (apk, att, b)
                break
        if pick is None:
            return None
        chosen.append(pick[0])
        chosen_bytes.add(pick[2])
        chosen_attrs |= pick[1]
    if not policy.is_satisfied_by(chosen_attrs):
        return None
    return chosen


def start_group(transport: TransportPort, creds: UserCredentials, apkL: list | None):
    if not apkL:
        return None
    pp = transport.pp
    dspk, cred = as_scheme.derive_pk(pp.aspp, creds.as_keys.pk)
    dssk = as_scheme.derive_sk(pp.aspp, creds.as_keys.sk, cred)
    subject = _member_tuple(pp, creds.gs_key, dspk, dssk)
    offers = []
    for apk in apkL:
        dapk, acred = as_scheme.derive_pk(pp.aspp, apk)
        offers.append(AdvisorOffer(dapk=dapk, cred=acred))
    tok = creds.tokens.take()
    shl = transport.ledger_add(tok, GroupEntry(subject=subject, offers=offers))
    if shl is None:
        return None
    return BubbleHandle(tok=tok, shl=shl, dspk=dspk, dssk=dssk, apkL=list(apkL))


def find_offer(transport: TransportPort, creds: UserCredentials, shl: int) -> int | None:
    pp = transport.pp
    grp = transport.ledger_get(shl)
    if not isinstance(grp, GroupEntry):
        return None
    for i, offer in enumerate(grp.offers):
        dask = as_scheme.derive_sk(pp.aspp, creds.as_keys.sk, offer.cred)
        if dask is not None and as_scheme.check(pp.aspp, offer.dapk, dask):
            return i
    return None


def join_group(transport: TransportPort, creds: UserCredentials, shl: int, idx: int):
    pp = transport.pp
    grp = transport.ledger_get(shl)
    if not isinstance(grp, GroupEntry) or not (0 <= idx < len(grp.offers)):
        return None
    offer = grp.offers[idx]
    dask = as_scheme.derive_sk(pp.aspp, creds.as_keys.sk, offer.cred)
    if dask is None:
        return None
    dapk = P.g1_mul(pp.aspp.g, dask)
    b1 = P.g1_eq(dapk, offer.dapk)
    b2 = as_scheme.check(pp.aspp, offer.dapk, dask)
    b3 = verify_member_tuple(pp, [], grp.subject)
    if not (b1 and b2 and b3):
        return None
    tok = creds.tokens.take()
    ahl = transport.ledger_add(tok, _member_tuple(pp, creds.gs_key, dapk, dask))
    if ahl is None:
        return None
    return JoinResult(ahl=ahl, tok=tok, dask=dask, dapk=dapk)


def close_group(transport: TransportPort, handle: BubbleHandle) -> bool:
    return transport.ledger_update(handle.tok, handle.shl, None)


def remove_advisor(transport: TransportPort, handle: BubbleHandle, dapk_star: Any) -> list:
    grp = transport.ledger_get(handle.shl)
    if not isinstance(grp, GroupEntry):
        return handle.apkL
    target = P.g1_to_bytes(dapk_star)
    idx = next(
        (i for i, o in enumerate(grp.offers) if P.g1_to_bytes(o.dapk) == target), None
    )
    if idx is None:
        return handle.apkL
    offers = [o for i, o in enumerate(grp.offers) if i != idx]
    handle.apkL = [a for i, a in enumerate(handle.apkL) if i != idx]
    transport.ledger_update(handle.tok, handle.shl, GroupEntry(grp.subject, offers))
    return handle.apkL


def replace_advisor(
    transport: TransportPort, handle: BubbleHandle, dapk_star: Any, policy: Policy
) -> list:
    grp = transport.ledger_get(handle.shl)
    if not isinstance(grp, GroupEntry):
        return handle.apkL
    target = P.g1_to_bytes(dapk_star)
    idx = next(
        (i for i, o in enumerate(grp.offers) if P.g1_to_bytes(o.dapk) == target), None
    )
    if idx is None:
        return handle.apkL
    star_bytes = P.g1_to_bytes(handle.apkL[idx])
    kept_offers = [o for i, o in enumerate(grp.offers) if i != idx]
    kept_apkL = [a for i, a in enumerate(handle.apkL) if i != idx]
    directory = {P.g1_to_bytes(apk): frozenset(att) for apk, att in transport.list_advisors()}
    chosen_bytes = {P.g1_to_bytes(a) for a in kept_apkL}
    chosen_attrs: set = set()
    for b in chosen_bytes:
        chosen_attrs |= directory.get(b, frozenset())
    additions: list = []
    for clause in policy.clauses:
        if chosen_attrs & clause:
            continue
        pick = None
        for apk, att in transport.list_advisors():
            b = P.g1_to_bytes(apk)
            if b == star_bytes or b in chosen_bytes or not transport.is_available(b):
                continue
            if frozenset(att) & clause:
                pick = (apk, frozenset(att), b)
                break
        if pick is None:
            return handle.apkL
        additions.append(pick[0])
        chosen_bytes.add(pick[2])
        chosen_attrs |= pick[1]
    if not policy.is_satisfied_by(chosen_attrs):
        return handle.apkL
    pp = transport.pp
    offers = list(kept_offers)
    new_apkL = list(kept_apkL)
    for apk in additions:
        dapk, cred = as_scheme.derive_pk(pp.aspp, apk)
        offers.append(AdvisorOffer(dapk=dapk, cred=cred))
        new_apkL.append(apk)
    transport.ledger_update(handle.tok, handle.shl, GroupEntry(grp.subject, offers))
    handle.apkL = new_apkL
    return new_apkL


get_advisors = profiling.profile()(get_advisors)
start_group = profiling.profile()(start_group)
find_offer = profiling.profile()(find_offer)
join_group = profiling.profile()(join_group)
close_group = profiling.profile()(close_group)
remove_advisor = profiling.profile()(remove_advisor)
replace_advisor = profiling.profile()(replace_advisor)
