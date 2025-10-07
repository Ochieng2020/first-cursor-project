from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.types import TypeDecorator, String

from .config import get_settings


_VERSION = "v1"
_NONCE_BYTES = 12


def _get_key() -> bytes:
    return get_settings().get_encryption_key()


@dataclass
class EncryptedPayload:
    nonce: bytes
    ciphertext: bytes

    def to_token(self) -> str:
        return f"{_VERSION}:{base64.b64encode(self.nonce).decode()}:{base64.b64encode(self.ciphertext).decode()}"

    @staticmethod
    def from_token(token: str) -> "EncryptedPayload":
        try:
            version, nonce_b64, ct_b64 = token.split(":", 2)
            if version != _VERSION:
                raise ValueError("Unsupported encryption version")
            return EncryptedPayload(
                nonce=base64.b64decode(nonce_b64),
                ciphertext=base64.b64decode(ct_b64),
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid encrypted payload format") from exc


def encrypt_str(plaintext: str) -> str:
    if plaintext is None:
        return plaintext
    key = _get_key()
    nonce = os.urandom(_NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), associated_data=None)
    return EncryptedPayload(nonce, ciphertext).to_token()


def decrypt_str(token: str) -> str:
    if token is None:
        return token
    payload = EncryptedPayload.from_token(token)
    key = _get_key()
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(payload.nonce, payload.ciphertext, associated_data=None)
    return plaintext.decode()


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return value
        return encrypt_str(value)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return value
        try:
            return decrypt_str(value)
        except Exception:
            # If value is not encrypted (legacy), return as-is
            return value
