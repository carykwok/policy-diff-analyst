"""Mode B source whitelist. Hardcoded — never accept URLs from LLM output."""

from urllib.parse import urlparse

ALLOWED_DOMAINS = (
    "www.gov.cn",
    "www.news.cn",        # 新华社
    "www.people.com.cn",  # 人民网
    "www.pbc.gov.cn",     # 中国人民银行
)

# (file_type, year) -> list of source dicts with tier + URL template
_GOVT_WORK_REPORT_URLS = {
    # Users should verify these template URLs against gov.cn's actual publication pages
    # at runtime. The registry's job is to scope which domains we may access.
    "tier1_template": "https://www.gov.cn/premier/{year}-03/05/content_government_work_report.htm",
    "tier2_template": "https://www.news.cn/politics/{year}lh/govt_report.htm",
}

def get_sources(file_type: str, year: int) -> list[dict]:
    if file_type != "govt_work_report":
        raise ValueError(f"unsupported file_type: {file_type}")
    return [
        {"tier": 1, "url": _GOVT_WORK_REPORT_URLS["tier1_template"].format(year=year), "domain": "www.gov.cn"},
        {"tier": 2, "url": _GOVT_WORK_REPORT_URLS["tier2_template"].format(year=year), "domain": "www.news.cn"},
    ]

def is_allowed(url: str) -> bool:
    """Return True only if url is https and its host is in ALLOWED_DOMAINS exactly.

    Substring checks (dom in url) are bypassable (e.g., www.gov.cn.evil.com). Parse
    the URL and compare host via equality against the whitelist.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    return host in ALLOWED_DOMAINS
