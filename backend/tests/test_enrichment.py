"""External-evidence enrichment tests (Pillar 5). Offline/no-network."""
from __future__ import annotations

from app.engines import enrichment


def test_classify_ref():
    assert enrichment.classify_ref("https://github.com/alice/ml-framework") == "github"
    assert enrichment.classify_ref("https://orcid.org/0009-0002-5057-4910") == "orcid"
    assert enrichment.classify_ref("0009-0002-5057-4910") == "orcid"
    assert enrichment.classify_ref("https://doi.org/10.5281/zenodo.123456") == "doi"
    assert enrichment.classify_ref("10.5281/zenodo.123456") == "doi"
    assert enrichment.classify_ref("10202601003R") == "patent"
    assert enrichment.classify_ref("https://linkedin.com/in/someone") == "linkedin"
    assert enrichment.classify_ref("https://example.com/portfolio") == "web"


def test_empty_supplementary_yields_no_evidence():
    assert enrichment.enrich_supplementary({}) == []
    assert enrichment.enrich_supplementary(None) == []
    # extracted_text only (no links) -> nothing to enrich
    assert enrichment.enrich_supplementary({"extracted_text": "resume body"}) == []


def test_disabled_records_unverified_without_fetching():
    # enrichment_enabled defaults False -> no network, everything 'unverified'
    supp = {
        "portfolio_urls": ["https://github.com/alice/repo"],
        "publication_dois": ["10.5281/zenodo.999"],
        "patent_numbers": ["10202601003R"],
        "orcid": "0009-0002-5057-4910",
    }
    items = enrichment.enrich_supplementary(supp)
    assert len(items) == 4
    assert all(i["status"] == "unverified" for i in items)
    types = {i["source_type"] for i in items}
    assert types == {"github", "doi", "patent", "orcid"}
    # each carries a human-readable reason and never raises
    assert all("summary" in i for i in items)


def test_patent_note_is_unverified_with_register_guidance():
    note = enrichment._note_patent("10202601003R")
    assert note["status"] == "unverified"
    assert "IPOS" in note["summary"]
