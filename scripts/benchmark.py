from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from osb.adapters.server import CentralServer
from osb.crypto import as_scheme, be_scheme, gs_scheme
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
)
from osb.protocol.policy import Policy

POLICY = Policy.of({"cancer_specialist"}, {"legal_advisor"})


def bench(label, make, runs=3):
    samples = []
    for _ in range(runs):
        op = make()
        start = time.perf_counter()
        op()
        samples.append((time.perf_counter() - start) * 1000)
    print(
        f"{label:<18}{statistics.mean(samples):10.2f}{min(samples):10.2f}"
        f"{max(samples):10.2f}{runs:7}"
    )


def const(value):
    return lambda: value


def ready_bubble(extra_legal=False):
    server = CentralServer()
    cancer = register_user(server, "c", "x", frozenset({"cancer_specialist"}))
    legal = register_user(server, "l", "x", frozenset({"legal_advisor"}))
    if extra_legal:
        register_user(server, "l2", "x", frozenset({"legal_advisor"}))
    subject = register_user(server, "subj", "x")
    handle = start_group(server, subject, get_advisors(server, POLICY))
    return server, cancer, legal, subject, handle


def main():
    print("OSB benchmarks - milliseconds per call (BLS12-381, pure-Python py_ecc)\n")
    print(f"{'operation':<18}{'avg':>10}{'min':>10}{'max':>10}{'runs':>7}")
    print("-" * 55)

    aspp = as_scheme.setup()
    kp = as_scheme.keygen(aspp)
    dpk, cred = as_scheme.derive_pk(aspp, kp.pk)
    asig = as_scheme.sign(aspp, kp.sk, b"m")
    bench("AS.keygen", const(lambda: as_scheme.keygen(aspp)), 10)
    bench("AS.derive_pk", const(lambda: as_scheme.derive_pk(aspp, kp.pk)), 10)
    bench("AS.derive_sk", const(lambda: as_scheme.derive_sk(aspp, kp.sk, cred)), 10)
    bench("AS.sign", const(lambda: as_scheme.sign(aspp, kp.sk, b"m")), 10)
    bench("AS.verify", const(lambda: as_scheme.verify(aspp, kp.pk, b"m", asig)), 10)

    tpk, tsk = gs_scheme.keygen()
    cpk, csk = gs_scheme.join(tpk, tsk, P.rand_scalar())
    gsig = gs_scheme.sign(tpk, csk, b"m")
    bench("GS.join", const(lambda: gs_scheme.join(tpk, tsk, P.rand_scalar())), 10)
    bench("GS.sign", const(lambda: gs_scheme.sign(tpk, csk, b"m")), 5)
    bench("GS.verify", const(lambda: gs_scheme.verify(tpk, [], b"m", gsig)), 5)

    gpk, mem = be_scheme.setup(3)
    bect = be_scheme.encrypt(gpk, b"hello")
    bench("BE.setup(3)", const(lambda: be_scheme.setup(3)), 5)
    bench("BE.encrypt", const(lambda: be_scheme.encrypt(gpk, b"hello")), 5)
    bench("BE.decrypt", const(lambda: be_scheme.decrypt(mem[0], bect)), 5)

    print("-" * 55)
    bench("Setup", const(lambda: CentralServer()), 3)

    server = CentralServer()
    counter = [0]

    def make_register():
        counter[0] += 1
        return lambda: register_user(server, f"u{counter[0]}", "x")

    bench("Register", make_register, 3)

    directory = ready_bubble()[0]
    bench("getAdvisorsS", const(lambda: get_advisors(directory, POLICY)), 5)
    bench("startGroupS", lambda: _make_start(), 3)
    bench("joinGroupA", lambda: _make_join(), 3)
    bench("closeGroupS", lambda: _make_close(), 3)
    bench("removeAdvisorS", lambda: _make_remove(), 3)
    bench("replaceAdvisorS", lambda: _make_replace(), 3)
    bench("Trace", lambda: _make_trace(), 3)
    bench("Judge", lambda: _make_judge(), 3)


def _make_start():
    server, _, _, subject, _ = ready_bubble()
    apkL = get_advisors(server, POLICY)
    return lambda: start_group(server, subject, apkL)


def _make_join():
    server, cancer, _, _, handle = ready_bubble()
    idx = find_offer(server, cancer, handle.shl)
    return lambda: join_group(server, cancer, handle.shl, idx)


def _make_close():
    server, _, _, _, handle = ready_bubble()
    return lambda: close_group(server, handle)


def _make_remove():
    server, _, _, _, handle = ready_bubble()
    dapk = server.ledger_get(handle.shl).offers[0].dapk
    return lambda: remove_advisor(server, handle, dapk)


def _make_replace():
    server, _, _, _, handle = ready_bubble(extra_legal=True)
    dapk = server.ledger_get(handle.shl).offers[1].dapk
    return lambda: replace_advisor(server, handle, dapk, POLICY)


def _make_trace():
    server, _, _, _, handle = ready_bubble()
    return lambda: server.osb_trace(handle.dspk)


def _make_judge():
    server, _, _, _, handle = ready_bubble()
    cpk = server.osb_trace(handle.dspk)
    return lambda: server.judge(cpk)


if __name__ == "__main__":
    main()
