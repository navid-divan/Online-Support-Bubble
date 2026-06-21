from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from osb.crypto import as_scheme, gs_scheme
from osb.crypto.primitives import schnorr
from osb.protocol.models.tokens import TokenList


@dataclass(frozen=True)
class RegistrationTuple:  # the tup sent to registrar
    spk: Any  # public key
    gsig: gs_scheme.GSSignature
    sig: schnorr.SchnorrSig


@dataclass(frozen=True)
class UserCredentials:
    as_keys: as_scheme.ASKeyPair  # subject or advisor keypair
    gs_key: gs_scheme.GSSignKey  # group signing key
    tokens: TokenList  # ledger write tokens

    @property
    def cpk(self) -> Any:
        return self.gs_key.A

    @property
    def public_key(self) -> Any:
        return self.as_keys.pk


@dataclass(frozen=True)
class UserRecord:  # stored privately by registrar
    upi: Any
    gsig: gs_scheme.GSSignature
    spk: Any
