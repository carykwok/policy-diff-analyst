import pytest
from scripts.source_registry import get_sources, ALLOWED_DOMAINS, is_allowed

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
