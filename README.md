# Online Support Bubble

This is a proof-of-concept implementation of paper "_Online Support Bubble: a Privacy Preserving Support Group Mechanism_".

In this repository, we have provided three interfaces: [terminal-based](https://github.com/navid-divan/Online-Support-Bubble) in this current directory (where it can get run via `./run.sh`), [graphical user interface](https://github.com/navid-divan/Online-Support-Bubble/tree/main/GUI) via the web application (where it can run by opening the [index.html](https://github.com/navid-divan/Online-Support-Bubble/blob/main/GUI/index.html) in the browser), and the mobile phone [Android application](https://github.com/navid-divan/Online-Support-Bubble/tree/main/android) (where it can run by installing the [apk file](https://github.com/navid-divan/Online-Support-Bubble/blob/main/android/OnlineSupportBubble-debug.apk) on the phone).

For all three interfaces, two files get generated to record the time and space costs for each functions.
* **`time_log`**: wall-clock time per instrumented function, in seconds, sorted by cumulative time.
  `cumulative_s` includes callees; `self_s` is the function's own time.
* **`space_log`**: memory attributed per instrumented function, sorted by cumulative usage.

An *online support bubble* lets a **subject** (a person seeking sensitive help) assemble an
anonymous group of **advisors** chosen by their *attributes*, e.g. `cancer_specialist`,
`legal_advisor`, ask questions, and receive auditable answers, while the
system guarantees:

* **Unlinkability**: nobody can link a user across different support bubbles, nor tell whether
  a given person is in any bubble at all.
* **Non-frameability**: nobody (not even the moderators) can impersonate an honest user or frame
  them for messages they did not send.
* **Accountable tracing**: a misbehaving member *can* be de-anonymised, but only when two
  independent authorities (the **Registrar** and the **Tracer**) cooperate.

To keep the demonstration tangible, here, because the ledger is accessed through a port, swapping the centralized server for a real distributed ledger later would not touch any protocol or cryptographic code.

### Cryptographic building blocks
All schemes run over the **BLS12-381** pairing-friendly curve via the
[`py_ecc`](https://github.com/ethereum/py_ecc) library (`optimized_bls12_381`). The library is
isolated behind `crypto/primitives/pairing.py`, which is the only file that imports it. `hash_to_g2` uses the RFC 9380 (`hash-to-curve`) implementation shipped with `py_ecc`.
| Scheme | File | Construction | Hard problem |
|--------|------|--------------|--------------|
| **AS**: Asynchronous Remote Key Generation | `crypto/as_scheme` | Discrete-log ARKG in G1: `dpk = pk·g^ck`, `ck = H(DH-secret)`, credential authenticated with HMAC | CDH / GDH in G1 |
| **GS**: Group Signature w/ Verifier-Local Revocation | `crypto/gs_scheme` | SDH membership credential `A = g1^{1/(γ+x)}` + Fiat–Shamir NIZK over a re-randomized `Â = A^t`; revocation tag `(Â, η^t)` with `η = hash_to_g2(m‖nonce)` | q-SDH in G1, ROM |
| **BE**: Public-key Broadcast Encryption | `crypto/be_scheme` | Boneh–Gentry–Waters "basic" scheme, broadcasting to the full member set; type-III adaptation | q-BDHE |
| **Schnorr** signature | `crypto/primitives/schnorr.py` | Key-prefixed Schnorr over G1 (used by AS for signing) | DLog in G1, ROM |
| **AEAD** | `crypto/primitives/aead.py` | Encrypt-then-MAC (SHA-256 keystream + HMAC-SHA-256), stdlib only, for the symmetric layer of BE | — |

### Protocol entities
| Entity | Responsibility |
|--------|----------------|
| **Registrar** | Onboards users, verifies their registration (`GS.Vf ∧ AS.Vf`), keeps the private identity map `uL` and the public permitted-key list `PKL`. Runs `Judge` during tracing. |
| **Tracer** | Holds the group-signature manager key `tsk`, issues group keys at registration, maintains the public revocation list `cpkL`, runs `Trace`. |
| **Ledger** | The append-only public store + authorisation-token accounting (`Register`, `Add`, `Get`, `Update`, `Search`). Tokens bind a location to its creator so only the creator can later update/close it. |
| **Subject / Advisor** | Client-side actors (`entities/subject`, `entities/advisor`), facades over the protocol algorithms. A subject builds and moderates bubbles; advisors join by attribute.

Tracing is intentionally split: the **Tracer** recovers a revocation token from a signature, and only
the **Registrar** can map that token back to a real identity. Neither can de-anonymise a user alone.

## Installation
Our implementation requires **Python ≥ 3.10**. From the `osb/` directory:
```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"     # installs py_ecc and pytest
```
This also installs an `osb` console command. The examples below use `python -m osb`, which works
without activating the venv.

## Usage
A `run.sh` script sits in this directory. It creates the virtualenv and
installs on first use, then launches:
```bash
./run.sh          # interactive shell (the app) - pre-loads sample users
./run.sh demo     # scripted end-to-end walkthrough
./run.sh test     # the full test suite
./run.sh info     # build / curve info
```

### Quick info

```bash
.venv/bin/python -m osb info
```

## Testing and Benchmarking
```bash
.venv/bin/python -m pytest
```
The suite (105 tests) covers the cryptographic primitives (correctness, unforgeability,
unlinkability, revocation, broadcast round-trips), the protocol layer (policy, ledger, registrar,
tracer), and end-to-end flows (registration, bubble formation, messaging, moderation, tracing) plus
the security-property checks in `tests/e2e/test_security.py`. For benchmarking:
```bash
.venv/bin/python scripts/benchmark.py
```
