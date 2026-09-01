"""Document extraction tests (A1)."""
from __future__ import annotations

import pytest

from app.engines.extract import ExtractionError, extract_text


def test_txt_extraction_and_normalization():
    raw = b"John Doe\n\n\n\nSenior Engineer   \n\n  Built things  "
    out = extract_text(raw, "txt")
    assert "John Doe" in out
    assert "Senior Engineer" in out
    # collapses 4 blank lines to a single blank
    assert "\n\n\n" not in out


def test_empty_text_rejected():
    with pytest.raises(ExtractionError):
        extract_text(b"   \n\n  ", "txt")


def test_unsupported_type_rejected():
    with pytest.raises(ExtractionError):
        extract_text(b"data", "rtf")


def test_docx_extraction_if_available():
    docx = pytest.importorskip("docx")
    import io

    document = docx.Document()
    document.add_paragraph("Jane Smith")
    document.add_paragraph("Principal Engineer")
    buf = io.BytesIO()
    document.save(buf)
    out = extract_text(buf.getvalue(), "docx")
    assert "Jane Smith" in out
    assert "Principal Engineer" in out
