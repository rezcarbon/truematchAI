"""SQLAlchemy column types that transparently encrypt/decrypt at the ORM layer.

Ciphertext is opaque text, so encrypted columns are stored as TEXT regardless of
the logical type. `EncryptedJSON` serializes to JSON before encrypting and parses
on read, so application code keeps working with dicts/lists.

For queryable fields (status codes, enums, categorical values), use Deterministic*
types which apply HMAC-SHA256 for searchable equality (==, IS NULL) without exposing
plaintext. These hash to the same value for the same input, enabling queries, but
the original value cannot be recovered.

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
    """A text column encrypted at rest using AES-256-GCM.

    Provides irreversible encryption (nonce is randomized per encryption).
    Use for sensitive narratives and free-form text that does not need to be
    queried. For queryable fields, use DeterministicEncryptedText instead.
    """

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
    """A JSON value (dict/list) encrypted at rest and stored as text.

    Provides irreversible encryption using AES-256-GCM (nonce is randomized).
    Use for complex nested sensitive data that does not need to be queried.
    """

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


class DeterministicEncryptedText(TypeDecorator):
    """A text column with deterministic encryption using HMAC-SHA256.

    Stores the deterministic HMAC hash of the value, enabling equality (==) and
    IS NULL queries without decryption or plaintext exposure. The same input
    always produces the same hash.

    Use for queryable fields like status codes, enums, and categorical values.
    The original plaintext cannot be recovered from the hash.

    Example:
        status: Mapped[str] = mapped_column(DeterministicEncryptedText(), nullable=True)

    Queries work transparently:
        session.query(Model).filter(Model.status == "active").all()
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.blind_index(str(value))

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        # The stored value is already the HMAC hash; return it directly.
        # It is not decryptable by design (used for queries only).
        if value is None:
            return None
        return value


class DeterministicEncryptedJSON(TypeDecorator):
    """A JSON value with deterministic encryption using HMAC-SHA256.

    Serializes the JSON to a canonical string, then stores the deterministic
    HMAC hash of that string. Enables equality (==) and IS NULL queries on
    JSON objects without decryption.

    Use for queryable JSON structures like status objects or categorical configs.
    The original plaintext cannot be recovered from the hash.

    Example:
        governance_metadata: Mapped[dict] = mapped_column(
            DeterministicEncryptedJSON(), nullable=True
        )
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        json_str = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return crypto.blind_index(json_str)

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        # The stored value is already the HMAC hash; return it directly.
        # It is not decryptable by design (used for queries only).
        if value is None:
            return None
        return value
