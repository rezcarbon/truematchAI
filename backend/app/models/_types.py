"""SQLAlchemy column types that transparently encrypt/decrypt at the ORM layer.

Ciphertext is opaque text, so encrypted columns are stored as TEXT regardless of
the logical type. `EncryptedJSON` serializes to JSON before encrypting and parses
on read, so application code keeps working with dicts/lists.

Reads tolerate legacy plaintext (values written while encryption was disabled),
which keeps dev data and pre-encryption rows readable. See app.core.crypto.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core import crypto


class EncryptedText(TypeDecorator):
    """A text column encrypted at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.encrypt(str(value))

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.decrypt(value)


class EncryptedJSON(TypeDecorator):
    """A JSON value (dict/list) encrypted at rest and stored as text."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.encrypt(json.dumps(value, ensure_ascii=False))

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        plaintext = crypto.decrypt(value)
        if plaintext is None:
            return None
        return json.loads(plaintext)
