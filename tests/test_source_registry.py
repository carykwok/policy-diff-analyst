import pytest
from scripts.source_registry import get_sources, get_search_hint, ALLOWED_DOMAINS, SUPPORTED_FILE_TYPES, is_allowed

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

@pytest.mark.parametrize("file_type", ["cewc", "five_year_plan", "third_plenum"])
def test_new_file_types_return_whitelisted_sources(file_type):
    sources = get_sources(file_type, 2024)
    assert len(sources) >= 1
    assert all(s["domain"] in ALLOWED_DOMAINS for s in sources)

def test_monetary_policy_report_sources_with_quarter():
    sources = get_sources("monetary_policy_report", 2024, quarter=1)
    assert len(sources) >= 1
    assert all(s["domain"] in ALLOWED_DOMAINS for s in sources)
    assert any("Q1" in s["url"] for s in sources)

def test_supported_file_types_tuple():
    assert len(SUPPORTED_FILE_TYPES) == 5
    assert "govt_work_report" in SUPPORTED_FILE_TYPES
    assert "cewc" in SUPPORTED_FILE_TYPES

def test_is_allowed_rejects_spoofed_and_non_https_urls():
    # Exact-host whitelisted
    assert is_allowed("https://www.gov.cn/premier/2024-03/05/report.htm") is True
    assert is_allowed("https://www.news.cn/politics/2024lh/govt_report.htm") is True
    # Case-insensitive host
    assert is_allowed("https://WWW.GOV.CN/path") is True
    # Spoofing attempts
    assert is_allowed("https://www.gov.cn.evil.com/path") is False
    assert is_allowed("https://evil.com/www.gov.cn/fake.htm") is False
    assert is_allowed("https://www.gov.cn@evil.com/") is False
    assert is_allowed("https://evil.com?x=www.gov.cn") is False
    # Non-https
    assert is_allowed("http://www.gov.cn/path") is False
    # Subdomains not explicitly whitelisted
    assert is_allowed("https://sub.www.gov.cn/path") is False
    # Non-whitelisted domains
    assert is_allowed("https://www.example.com/path") is False
    # Malformed / empty
    assert is_allowed("") is False
    assert is_allowed("not a url") is False


def test_get_search_hint_returns_query():
    hint = get_search_hint("govt_work_report", 2025)
    assert "2025" in hint
    assert "政府工作报告" in hint
    assert "gov.cn" in hint


def test_get_search_hint_monetary_with_quarter():
    hint = get_search_hint("monetary_policy_report", 2024, quarter=3)
    assert "2024" in hint
    assert "3" in hint
    assert "pbc.gov.cn" in hint


def test_get_search_hint_unsupported_raises():
    with pytest.raises(ValueError, match="unsupported file_type"):
        get_search_hint("unknown_type", 2024)
