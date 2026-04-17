"""Mode B source whitelist. Hardcoded — never accept URLs from LLM output."""

from urllib.parse import urlparse

ALLOWED_DOMAINS = (
    "www.gov.cn",
    "www.news.cn",        # 新华社
    "www.people.com.cn",  # 人民网
    "www.pbc.gov.cn",     # 中国人民银行
)

SUPPORTED_FILE_TYPES = (
    "govt_work_report",
    "cewc",
    "five_year_plan",
    "third_plenum",
    "monetary_policy_report",
)

_URL_TEMPLATES: dict[str, list[dict]] = {
    "govt_work_report": [
        {"tier": 1, "template": "https://www.gov.cn/premier/{year}-03/05/content_government_work_report.htm", "domain": "www.gov.cn"},
        {"tier": 2, "template": "https://www.news.cn/politics/{year}lh/govt_report.htm", "domain": "www.news.cn"},
    ],
    "cewc": [
        {"tier": 1, "template": "https://www.gov.cn/yaowen/liebiao/{year}12/cewc.htm", "domain": "www.gov.cn"},
        {"tier": 2, "template": "https://www.news.cn/politics/{year}-12/cewc.htm", "domain": "www.news.cn"},
    ],
    "five_year_plan": [
        {"tier": 1, "template": "https://www.gov.cn/xinwen/{year}-03/five_year_plan.htm", "domain": "www.gov.cn"},
        {"tier": 2, "template": "https://www.news.cn/politics/{year}lh/five_year_plan.htm", "domain": "www.news.cn"},
    ],
    "third_plenum": [
        {"tier": 1, "template": "https://www.gov.cn/zhengce/{year}/third_plenum_decision.htm", "domain": "www.gov.cn"},
        {"tier": 2, "template": "https://www.news.cn/politics/{year}/third_plenum.htm", "domain": "www.news.cn"},
    ],
    "monetary_policy_report": [
        {"tier": 1, "template": "https://www.pbc.gov.cn/zhengcehuobisi/{year}Q{quarter}/mpr.htm", "domain": "www.pbc.gov.cn"},
        {"tier": 2, "template": "https://www.gov.cn/xinwen/{year}/mpr_Q{quarter}.htm", "domain": "www.gov.cn"},
    ],
}

def get_sources(file_type: str, year: int, **kwargs) -> list[dict]:
    if file_type not in _URL_TEMPLATES:
        raise ValueError(f"unsupported file_type: {file_type}")
    return [
        {"tier": t["tier"], "url": t["template"].format(year=year, **kwargs), "domain": t["domain"]}
        for t in _URL_TEMPLATES[file_type]
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
