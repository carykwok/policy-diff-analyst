import pytest
from scripts.source_registry import get_sources, ALLOWED_DOMAINS

def test_govt_work_report_sources_returned_for_year():
    sources = get_sources("govt_work_report", 2024)
    assert len(sources) >= 1
    assert all(s["tier"] in (1, 2) for s in sources)
    assert all(any(dom in s["url"] for dom in ALLOWED_DOMAINS) for s in sources)
    tiers = [s["tier"] for s in sources]
    assert tiers == sorted(tiers), "Tier 1 must come before Tier 2"

def test_unsupported_file_type_raises():
    with pytest.raises(ValueError, match="unsupported file_type"):
        get_sources("unknown_type", 2024)

def test_allowed_domains_are_authoritative_only():
    for dom in ALLOWED_DOMAINS:
        assert dom.endswith(".gov.cn") or dom.endswith(".cn") or dom.endswith(".com.cn")
