"""Mode B source whitelist. Hardcoded — never accept URLs from LLM output.

Two discovery strategies:
1. Template URLs: pre-built URL patterns (may 404, used as first attempt)
2. Search hints: query strings for WebSearch to find actual URLs
   (LLM uses these to discover real URLs, then validates against ALLOWED_DOMAINS)
"""

from urllib.parse import urlparse

ALLOWED_DOMAINS = (
    "www.gov.cn",
    "www.news.cn",        # 新华社
    "www.people.com.cn",  # 人民网
    "www.pbc.gov.cn",     # 中国人民���行
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

_SEARCH_HINTS: dict[str, str] = {
    "govt_work_report": "{year}年政府工作报告全文 site:gov.cn",
    "cewc": "{year}年中央经济工作会议 全文 site:gov.cn",
    "five_year_plan": "十{plan_ord}五规划纲要 全文 site:gov.cn",
    "third_plenum": "{year}年三中全会决定 全文 site:gov.cn",
    "monetary_policy_report": "{year}年第{quarter}季度货币政策执行报告 site:pbc.gov.cn",
}


def get_search_hint(file_type: str, year: int, **kwargs) -> str:
    """Return a search query string for discovering the actual document URL.

    The LLM should use this with WebSearch, pick URLs from results,
    validate each with is_allowed(), then fetch the valid ones.
    """
    if file_type not in _SEARCH_HINTS:
        raise ValueError(f"unsupported file_type: {file_type}")
    return _SEARCH_HINTS[file_type].format(year=year, **kwargs)


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
