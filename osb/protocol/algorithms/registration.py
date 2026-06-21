from __future__ import annotations

from typing import Any

from osb import profiling
from osb.config.attributes import validate_all
from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import pairing as P
from osb.protocol.models.params import PublicParams
from osb.protocol.models.registration import RegistrationTuple, UserCredentials


def register_user(server: Any, u: Any, upi: Any, att: Any = None) -> UserCredentials | None:
    if att:
        validate_all(att)
    pp: PublicParams = server.pp
    kp = as_scheme.keygen(pp.aspp)
    r = P.rand_scalar()  # blinding for the tracer
    cpk, csk = server.tracer_join(r)
    gsig = gs_scheme.sign(pp.tpk, csk, P.g1_to_bytes(kp.pk))
    sig = as_scheme.sign(pp.aspp, kp.sk, gs_scheme.sig_to_bytes(gsig))
    tup = RegistrationTuple(spk=kp.pk, gsig=gsig, sig=sig)
    tokens = server.register(u, upi, att, tup)
    if tokens is None:
        return None
    return UserCredentials(as_keys=kp, gs_key=csk, tokens=tokens)


register_user = profiling.profile()(register_user)
