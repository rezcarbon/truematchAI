"""Field-level encryption tests (A4)."""
from __future__ import annotations

import base64

import pytest

from app.core import crypto
from app.models._types import EncryptedJSON, EncryptedText

_KEY = base64.b64encode(b"A" * 32).decode()


@pytest.fixture
def encryption_on(monkeypatch):
    monkeypatch.setattr(crypto.settings, "encryption_key", _KEY)
    monkeypatch.setattr(crypto.settings, "encryption_index_key", "")
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()
    yield
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()


@pytest.fixture
def encryption_off(monkeypatch):
    monkeypatch.setattr(crypto.settings, "encryption_key", "")
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()
    yield
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()


def test_disabled_passthrough(encryption_off):
    assert crypto.encryption_enabled() is False
    assert crypto.encrypt("hello") == "hello"
    assert crypto.decrypt("hello") == "hello"
    assert crypto.encrypt(None) is None


def test_enabled_roundtrip(encryption_on):
    assert crypto.encryption_enabled() is True
    token = crypto.encrypt("sensitive resume text")
    assert token.startswith("enc:v1:")
    assert "sensitive" not in token
    assert crypto.decrypt(token) == "sensitive resume text"


def test_nonce_makes_ciphertext_unique(encryption_on):
    assert crypto.encrypt("same") != crypto.encrypt("same")


def test_decrypt_tampered_raises(encryption_on):
    token = crypto.encrypt("x")
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt(tampered)


def test_decrypt_encrypted_without_key_raises(monkeypatch):
    # Encrypt with a key...
    monkeypatch.setattr(crypto.settings, "encryption_key", _KEY)
    crypto._dek.cache_clear()
    token = crypto.encrypt("x")
    # ...then simulate the key being absent at read time.
    monkeypatch.setattr(crypto.settings, "encryption_key", "")
    crypto._dek.cache_clear()
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt(token)
    crypto._dek.cache_clear()


def test_legacy_plaintext_passthrough_on_decrypt(encryption_on):
    # A value stored before encryption was enabled has no prefix.
    assert crypto.decrypt("legacy-plaintext") == "legacy-plaintext"


def test_blind_index_deterministic_and_case_insensitive(encryption_on):
    a = crypto.blind_index("U-ABC-123")
    b = crypto.blind_index("u-abc-123")
    assert a == b
    assert a != "u-abc-123"  # not the raw value
    assert crypto.blind_index(None) is None


def test_encrypted_text_typedecorator_roundtrip(encryption_on):
    t = EncryptedText()
    bound = t.process_bind_param("notes about candidate", None)
    assert bound.startswith("enc:v1:")
    assert t.process_result_value(bound, None) == "notes about candidate"
    assert t.process_bind_param(None, None) is None


def test_encrypted_json_typedecorator_roundtrip(encryption_on):
    t = EncryptedJSON()
    payload = {"extracted_text": "Maya — 7 years ML", "skills": ["python"]}
    bound = t.process_bind_param(payload, None)
    assert bound.startswith("enc:v1:")
    assert "Maya" not in bound
    assert t.process_result_value(bound, None) == payload


def test_encryption_at_rest_through_real_engine(encryption_on):
    """Round-trip through an actual SQLAlchemy engine: the stored bytes are
    ciphertext, while ORM/Core reads transparently decrypt."""
    from sqlalchemy import Column, MetaData, String, Table, create_engine, insert, select, text

    engine = create_engine("sqlite://")
    md = MetaData()
    tbl = Table(
        "t",
        md,
        Column("id", String, primary_key=True),
        Column("notes", EncryptedText),
        Column("blob", EncryptedJSON),
    )
    md.create_all(engine)
    with engine.begin() as c:
        c.execute(
            insert(tbl).values(id="1", notes="secret note", blob={"x": "resume text"})
        )
    with engine.connect() as c:
        raw_notes, raw_blob = c.execute(text("SELECT notes, blob FROM t")).one()
        assert raw_notes.startswith("enc:v1:") and "secret" not in raw_notes
        assert raw_blob.startswith("enc:v1:") and "resume" not in raw_blob
        typed = c.execute(select(tbl.c.notes, tbl.c.blob)).one()
        assert typed[0] == "secret note"
        assert typed[1] == {"x": "resume text"}
