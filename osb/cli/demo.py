from __future__ import annotations

from osb.cli.session import World


def _step(title: str) -> None:
    print(f"\n=== {title} ===")


def run_demo() -> int:
    print("Online Support Bubble - end-to-end demo")
    print("(real BLS12-381 pairing crypto in pure Python - expect ~30-60s)")
    w = World()

    _step("1. sample users (Emma is a patient; the rest are advisors)")
    print(w.seed())
    print(w.list_advisors())

    _step("2. Emma forms a bubble: needs a cancer specialist AND a legal advisor")
    print(w.create_bubble("emma", "cancer_specialist;legal_advisor"))

    _step("3. the invited advisors join")
    print(w.join("b0", "walker"))
    print(w.join("b0", "bennett"))

    _step("4. sign-then-encrypt broadcast messaging")
    print(w.send("b0", "emma", "I was just diagnosed - what are my options?"))
    print(w.send("b0", "walker", "Several; let us review them carefully."))
    print(w.send("b0", "bennett", "I can advise on your medical-leave rights."))
    print(w.inbox("b0", "emma"))

    _step("5. replace one advisor; the replacement joins")
    print(w.replace("b0", "bennett"))
    print(w.join("b0", "marsh"))

    _step("6. trace a member (Registrar + Tracer must collaborate)")
    print(w.trace("b0", "walker"))

    _step("7. close the bubble")
    print(w.close("b0"))
    print(w.overview())

    print("\n(time_log and space_log were written to the current directory.)")
    return 0
