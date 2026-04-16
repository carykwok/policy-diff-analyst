# Policy Diff Analyst Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill `policy-diff-analyst` that compares two (or N) versions of Chinese policy documents (首发 govt_work_report), produces Word + Excel + PNG charts deliverables with MECE framework coverage.

**Architecture:** Main SKILL.md orchestrates; Python scripts handle deterministic work (parse/diff/score/chart/xlsx/docx); LLM produces article prose (style-guided); Mode A takes user-supplied inputs, Mode B auto-fetches from hardcoded source whitelist.

**Tech Stack:** Python 3.11+, pytest, python-docx, openpyxl, matplotlib, plotly, pypdf, requests, beautifulsoup4, jieba (中文分词).

**Design Spec:** [docs/superpowers/specs/2026-04-16-policy-diff-analyst-design.md](../specs/2026-04-16-policy-diff-analyst-design.md)

---

## File Structure

```
policy-diff-analyst/
├── SKILL.md                           # Main skill entry (Claude reads this)
├── pyproject.toml                     # Python project config + deps
├── scripts/
│   ├── __init__.py
│   ├── models.py                      # Dataclasses: Document, Section, DiffReport, ...
│   ├── source_registry.py             # [Mode B] hardcoded source whitelist
│   ├── fetcher.py                     # [Mode B] fetch URL with cache + robots
│   ├── parse_input.py                 # Parse text / URL / PDF / .docx → Document
│   ├── diff_engine.py                 # A1–A7 structured diff
│   ├── score_model.py                 # B2: term frequency + strength scoring
│   ├── build_charts.py                # G1–G6 matplotlib/plotly → PNG
│   ├── build_xlsx.py                  # Excel data tables (4 sheets)
│   ├── build_docx.py                  # Word article assembler
│   └── run.py                         # CLI entry point orchestrating everything
├── references/
│   ├── profile_govt_work_report.md    # v1 profile (keywords, scoring anchors)
│   └── source_whitelist.md            # Human-readable whitelist doc
├── assets/
│   ├── style_research.md              # 投研派 writing guide
│   ├── style_media.md                 # 媒体派 writing guide
│   └── style_retail.md                # 投资派 writing guide
├── tests/
│   ├── __init__.py
│   ├── fixtures/                      # sample text/pdf/docx/html
│   └── test_*.py                      # one test file per script
└── evals/
    └── evals.json
```

**Design rationale:** Each script has a single responsibility. `models.py` defines shared dataclasses so types stay consistent across modules. Tests mirror scripts 1:1. Fixtures live in `tests/fixtures/` so every test is deterministic without network access.

---

## Task 0: Project Skeleton + Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `scripts/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "policy-diff-analyst"
version = "0.1.0"
description = "Claude Code skill for comparing Chinese policy documents"
requires-python = ">=3.11"
dependencies = [
    "python-docx>=1.1.0",
    "openpyxl>=3.1.0",
    "matplotlib>=3.8.0",
    "plotly>=5.18.0",
    "pypdf>=4.0.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "jieba>=0.42.1",
    "pandas>=2.1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-cov>=4.1.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: Create empty `__init__.py` files**

Create `scripts/__init__.py` and `tests/__init__.py` as zero-byte files.

- [ ] **Step 3: Create `tests/conftest.py`** (shared fixture root)

```python
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def fixtures_dir():
    return FIXTURES
```

- [ ] **Step 4: Install and smoke-test**

Run: `pip install -e ".[dev]" && pytest --collect-only`
Expected: `collected 0 items` (no tests yet, but pytest runs clean).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml scripts/ tests/
git commit -m "Add project skeleton with pyproject.toml and pytest harness"
```

---

## Task 1: Shared Data Models (`scripts/models.py`)

**Rationale:** Every other module produces or consumes `Document` / `DiffReport`. Define them once, centrally, to prevent type drift.

**Files:**
- Create: `scripts/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_models.py
from scripts.models import Document, Section, DiffItem, DiffReport, StrengthScore

def test_document_basic_construction():
    doc = Document(
        title="2024 政府工作报告",
        year=2024,
        file_type="govt_work_report",
        source_url="https://www.gov.cn/...",
        sections=[Section(heading="一、2023年工作回顾", body="...")],
        raw_text="全文..."
    )
    assert doc.year == 2024
    assert doc.sections[0].heading == "一、2023年工作回顾"

def test_diff_item_layers():
    item = DiffItem(layer="A1", change_type="modified", old="GDP 5.5%", new="GDP 5.0%", note="目标下调")
    assert item.layer == "A1"
    assert item.change_type in ("added", "removed", "modified", "kept")

def test_strength_score_range():
    s = StrengthScore(dimension="A3_产业", old=3.0, new=4.0)
    assert 0 <= s.old <= 5 and 0 <= s.new <= 5

def test_diff_report_aggregate():
    report = DiffReport(
        old_doc_title="2023",
        new_doc_title="2024",
        items=[DiffItem(layer="A1", change_type="added", old="", new="新质生产力", note="")],
        strength=[StrengthScore(dimension="A3_产业", old=3.0, new=4.0)],
        term_freq={"新质生产力": {"old": 0, "new": 12}},
    )
    assert len(report.items) == 1
```

- [ ] **Step 2: Run — expect import failure**

Run: `pytest tests/test_models.py -v`
Expected: ImportError — `scripts.models` does not exist.

- [ ] **Step 3: Implement `scripts/models.py`**

```python
from dataclasses import dataclass, field
from typing import Literal, Optional

@dataclass
class Section:
    heading: str
    body: str

@dataclass
class Document:
    title: str
    year: int
    file_type: str
    source_url: Optional[str]
    sections: list[Section]
    raw_text: str

ChangeType = Literal["added", "removed", "modified", "kept"]

@dataclass
class DiffItem:
    layer: str               # "A1" .. "A7"
    change_type: ChangeType
    old: str
    new: str
    note: str

@dataclass
class StrengthScore:
    dimension: str           # "A1_定调" | "A2_工具" | ... | "A6_区域对外"
    old: float               # 0.0–5.0
    new: float

@dataclass
class DiffReport:
    old_doc_title: str
    new_doc_title: str
    items: list[DiffItem]
    strength: list[StrengthScore]
    term_freq: dict[str, dict[str, int]]   # term -> {"old": n, "new": m}
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_models.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/models.py tests/test_models.py
git commit -m "Add shared data models for Document, DiffItem, DiffReport"
```

---

## Task 2: Source Registry (`scripts/source_registry.py`) — Mode B whitelist

**Rationale:** Hardcoded whitelist prevents prompt injection from steering fetcher to untrusted sources. Only returns Tier 1 / Tier 2 URLs derived from the file_type + year.

**Files:**
- Create: `scripts/source_registry.py`
- Create: `tests/test_source_registry.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_source_registry.py
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
    # Only whitelisted authoritative domains
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
```

- [ ] **Step 2: Run — expect import error**

Run: `pytest tests/test_source_registry.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/source_registry.py`**

```python
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
```

> Note: the literal URL templates above are approximations — production use will require updating templates to match actual publication URLs, but the registry's contract (whitelist enforcement + tiered return) is stable.

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_source_registry.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/source_registry.py tests/test_source_registry.py
git commit -m "Add Mode B source registry with hardcoded domain whitelist"
```

---

## Task 3: Fetcher (`scripts/fetcher.py`) — Mode B HTTP + cache

**Rationale:** Only URLs cleared by `source_registry.is_allowed` may be fetched. Results cached by SHA256(url) to avoid repeat hits. Respect robots.txt.

**Files:**
- Create: `scripts/fetcher.py`
- Create: `tests/test_fetcher.py`
- Create: `tests/fixtures/sample_gov_page.html`

- [ ] **Step 1: Create fixture**

`tests/fixtures/sample_gov_page.html`:
```html
<!DOCTYPE html>
<html><head><title>2024年政府工作报告</title></head>
<body><article>
<h1>2024 政府工作报告</h1>
<p>各位代表：现在，我代表国务院，向大会报告政府工作...</p>
<p>国内生产总值增长 5% 左右。</p>
</article></body></html>
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_fetcher.py
from unittest.mock import patch, MagicMock
import pytest
from scripts.fetcher import fetch, FetchError

def test_fetch_returns_text_and_caches(tmp_path, fixtures_dir):
    html = (fixtures_dir / "sample_gov_page.html").read_text(encoding="utf-8")
    mock_resp = MagicMock(status_code=200, text=html, content=html.encode("utf-8"))
    mock_resp.raise_for_status = MagicMock()
    with patch("scripts.fetcher.requests.get", return_value=mock_resp) as mock_get:
        text1 = fetch("https://www.gov.cn/test", cache_dir=tmp_path)
        text2 = fetch("https://www.gov.cn/test", cache_dir=tmp_path)
    assert "国内生产总值增长 5%" in text1
    assert text1 == text2
    assert mock_get.call_count == 1  # second call hits cache

def test_fetch_rejects_non_whitelisted_url(tmp_path):
    with pytest.raises(FetchError, match="not on whitelist"):
        fetch("https://evil.example.com/policy", cache_dir=tmp_path)

def test_fetch_http_error_raises(tmp_path):
    mock_resp = MagicMock(status_code=404)
    mock_resp.raise_for_status = MagicMock(side_effect=Exception("404"))
    with patch("scripts.fetcher.requests.get", return_value=mock_resp):
        with pytest.raises(FetchError):
            fetch("https://www.gov.cn/missing", cache_dir=tmp_path)
```

- [ ] **Step 3: Run — expect failure**

Run: `pytest tests/test_fetcher.py -v`
Expected: ImportError.

- [ ] **Step 4: Implement `scripts/fetcher.py`**

```python
import hashlib
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from scripts.source_registry import is_allowed

USER_AGENT = "policy-diff-analyst/0.1 (+https://github.com/carykwok/policy-diff-analyst)"
TIMEOUT = 20

class FetchError(RuntimeError):
    pass

def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

def fetch(url: str, cache_dir: Path) -> str:
    if not is_allowed(url):
        raise FetchError(f"URL not on whitelist: {url}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{_cache_key(url)}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        raise FetchError(f"fetch failed for {url}: {e}") from e
    soup = BeautifulSoup(resp.content, "lxml")
    # Extract article body — fall back to whole text if no <article>
    article = soup.find("article") or soup.find("body")
    text = article.get_text("\n", strip=True) if article else soup.get_text("\n", strip=True)
    cache_file.write_text(text, encoding="utf-8")
    return text
```

- [ ] **Step 5: Run — expect pass**

Run: `pytest tests/test_fetcher.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetcher.py tests/test_fetcher.py tests/fixtures/sample_gov_page.html
git commit -m "Add whitelisted HTTP fetcher with content cache"
```

---

## Task 4: Input Parser (`scripts/parse_input.py`) — 4 modalities

**Rationale:** Unify URL / PDF / .docx / raw text into a single `Document`. Keep section detection crude for v1 (numbered top-level headings).

**Files:**
- Create: `scripts/parse_input.py`
- Create: `tests/test_parse_input.py`
- Create: `tests/fixtures/sample_report.txt`
- Create: `tests/fixtures/sample_report.pdf` (minimal PDF produced by the test)
- Create: `tests/fixtures/sample_report.docx` (minimal Word produced by the test)

- [ ] **Step 1: Create text fixture**

`tests/fixtures/sample_report.txt`:
```
2024 政府工作报告

一、2023 年工作回顾
国内生产总值超过 126 万亿元，增长 5.2%。

二、2024 年经济社会发展总体要求和政策取向
今年发展主要预期目标是：国内生产总值增长 5% 左右。
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_parse_input.py
from pathlib import Path
from docx import Document as DocxDocument
from pypdf import PdfWriter
import pytest
from scripts.parse_input import parse_text, parse_docx, parse_pdf, detect_sections

def test_parse_text_extracts_title_and_sections(fixtures_dir):
    raw = (fixtures_dir / "sample_report.txt").read_text(encoding="utf-8")
    doc = parse_text(raw, year=2024, title="2024 政府工作报告")
    assert doc.year == 2024
    assert len(doc.sections) == 2
    assert doc.sections[0].heading.startswith("一、")
    assert "126 万亿元" in doc.sections[0].body

def test_detect_sections_numbered_chinese():
    body = "一、回顾\n去年 GDP 增长 5.2%\n二、展望\n今年目标 5% 左右"
    sections = detect_sections(body)
    assert len(sections) == 2
    assert sections[0].heading == "一、回顾"
    assert sections[1].body.startswith("今年目标")

def test_parse_docx_reads_paragraphs(tmp_path):
    docx_path = tmp_path / "sample.docx"
    d = DocxDocument()
    d.add_paragraph("2024 政府工作报告")
    d.add_paragraph("一、回顾")
    d.add_paragraph("GDP 5.2%")
    d.save(docx_path)
    doc = parse_docx(docx_path, year=2024)
    assert "GDP 5.2%" in doc.raw_text
    assert len(doc.sections) == 1

def test_parse_pdf_extracts_text(tmp_path):
    # Build minimal PDF via reportlab if available; fall back to pypdf blank
    pytest.importorskip("reportlab")
    from reportlab.pdfgen import canvas
    pdf_path = tmp_path / "sample.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "2024 政府工作报告")
    c.drawString(100, 730, "一、回顾")
    c.drawString(100, 710, "GDP 5.2%")
    c.save()
    doc = parse_pdf(pdf_path, year=2024)
    assert "GDP" in doc.raw_text
```

- [ ] **Step 3: Run — expect import error**

Run: `pytest tests/test_parse_input.py -v`
Expected: ImportError.

- [ ] **Step 4: Implement `scripts/parse_input.py`**

```python
import re
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument
from scripts.models import Document, Section

# Matches headings like "一、", "二、", "三、" at line start
_SECTION_HEADING_RE = re.compile(r"^[一二三四五六七八九十]+、.+", re.MULTILINE)

def detect_sections(body: str) -> list[Section]:
    matches = list(_SECTION_HEADING_RE.finditer(body))
    if not matches:
        return [Section(heading="全文", body=body.strip())]
    sections: list[Section] = []
    for i, m in enumerate(matches):
        heading_line = m.group(0).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections.append(Section(heading=heading_line, body=content))
    return sections

def parse_text(raw: str, *, year: int, title: str | None = None, source_url: str | None = None) -> Document:
    lines = raw.strip().splitlines()
    inferred_title = title or (lines[0].strip() if lines else "")
    body = "\n".join(lines[1:]) if title is None and lines else raw
    sections = detect_sections(body)
    return Document(
        title=inferred_title,
        year=year,
        file_type="govt_work_report",
        source_url=source_url,
        sections=sections,
        raw_text=raw,
    )

def parse_docx(path: Path, *, year: int, source_url: str | None = None) -> Document:
    d = DocxDocument(str(path))
    paras = [p.text for p in d.paragraphs if p.text.strip()]
    raw = "\n".join(paras)
    return parse_text(raw, year=year, title=paras[0] if paras else "", source_url=source_url)

def parse_pdf(path: Path, *, year: int, source_url: str | None = None) -> Document:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    raw = "\n".join(pages)
    return parse_text(raw, year=year, source_url=source_url)
```

- [ ] **Step 5: Run — expect pass** (install reportlab if PDF test needs it)

Run: `pip install reportlab && pytest tests/test_parse_input.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/parse_input.py tests/test_parse_input.py tests/fixtures/sample_report.txt
git commit -m "Add unified input parser for text, .docx, and PDF"
```

---

## Task 5: Profile Document (`references/profile_govt_work_report.md`)

**Rationale:** Diff engine and scorer read this to know which keywords map to which MECE layer and how to score strength. Keep it editable by hand.

**Files:**
- Create: `references/profile_govt_work_report.md`

- [ ] **Step 1: Write the profile**

```markdown
# Profile: 政府工作报告 (govt_work_report)

## Layer keyword maps (A1–A7)

### A1 宏观定调
- 量化指标关键词：GDP / 国内生产总值、赤字率、CPI / 居民消费价格、城镇新增就业
- 基调锚定短语：稳中求进、稳中有进、高质量发展、以进促稳

### A2 政策工具
- 货币：稳健、灵活适度、精准有力、降准、降息、结构性货币政策工具
- 财政：赤字率、专项债、超长期特别国债、减税降费

### A3 产业地图
- 科技：新质生产力、人工智能、AI、算力、半导体、集成电路、量子、生物制造
- 制造：新能源、智能制造、高端装备、工业母机
- 安全：能源安全、粮食安全、产业链供应链、国产替代
- 消费：汽车、地产、服务消费、文旅

### A4 风险监管
- 房地产、地方债务、金融风险、平台经济、防范化解

### A5 民生分配
- 居民收入、社保、医保、养老、生育、教育、医疗

### A6 区域对外
- 区域：京津冀、长三角、粤港澳、成渝、东北、西部
- 对外：对外开放、一带一路、外资、进博会

### A7 结构增量
横切层，由 diff 引擎基于 A1-A6 的 added/removed/intensity_shift 自动聚合。

## Strength scoring anchors (0–5 scale)

Applied to verbs/modifiers in each layer to compute B2 scores:

| 措辞 | 得分 |
|------|------|
| 坚决、坚定、全面 | 5 |
| 大力、着力、切实 | 4 |
| 加快、积极、深入 | 3 |
| 稳妥、有序、逐步 | 2 |
| 审慎、适度、研究 | 1 |
| (未提及) | 0 |

Scoring rule: for each A1–A6 layer, aggregate the highest-scoring modifier within ±10 Chinese characters of any layer keyword. Mean across all hits = layer score.

## Notes
- This profile is v1 for 政府工作报告 only. Later profiles override/extend.
- Keep keyword list focused — max 10 per layer sub-bucket to avoid noise.
```

- [ ] **Step 2: Commit**

```bash
git add references/profile_govt_work_report.md
git commit -m "Add govt_work_report profile with MECE keyword maps and scoring anchors"
```

---

## Task 6: Diff Engine (`scripts/diff_engine.py`)

**Rationale:** Classifies every keyword hit into one of A1–A6 with a change_type; derives A7 (added/removed/intensity shifts) by aggregation.

**Files:**
- Create: `scripts/diff_engine.py`
- Create: `tests/test_diff_engine.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_diff_engine.py
from scripts.models import Document, Section
from scripts.diff_engine import load_profile, compute_diff

PROFILE_PATH = "references/profile_govt_work_report.md"

def _doc(year, text):
    return Document(
        title=f"{year} 政府工作报告",
        year=year,
        file_type="govt_work_report",
        source_url=None,
        sections=[Section(heading="一、回顾", body=text)],
        raw_text=text,
    )

def test_load_profile_returns_layer_keywords():
    profile = load_profile(PROFILE_PATH)
    assert "新质生产力" in profile.keywords_by_layer["A3"]
    assert "房地产" in profile.keywords_by_layer["A4"]
    assert profile.strength_scale["大力"] == 4

def test_compute_diff_detects_added_and_removed_terms():
    old = _doc(2023, "GDP 增长 5.5%，积极稳妥化解房地产风险。")
    new = _doc(2024, "GDP 增长 5% 左右，大力发展新质生产力，坚决防范房地产风险。")
    profile = load_profile(PROFILE_PATH)
    report = compute_diff(old, new, profile)

    layers_seen = {item.layer for item in report.items}
    # A3 gets 'added' items (新质生产力); A4 intensity shifts (积极稳妥→坚决 around 房地产)
    assert "A3" in layers_seen
    assert "A4" in layers_seen
    assert "A7" in layers_seen       # aggregate summary always present

    added = [i for i in report.items if i.change_type == "added"]
    assert any("新质生产力" in i.new for i in added)

    a4_items = [i for i in report.items if i.layer == "A4" and i.change_type == "modified"]
    assert any("强度" in i.note for i in a4_items)
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_diff_engine.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/diff_engine.py`**

```python
import re
from dataclasses import dataclass
from pathlib import Path
from scripts.models import Document, DiffItem, DiffReport, StrengthScore

@dataclass
class Profile:
    keywords_by_layer: dict[str, list[str]]      # "A1" -> [kw, ...]
    strength_scale: dict[str, int]               # "大力" -> 4

_LAYER_SECTION_RE = re.compile(r"^### (A[1-7])\s+(.+)$", re.MULTILINE)
_BULLET_KW_RE = re.compile(r"[：:]\s*(.+)$")
_SCALE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d+)\s*\|")

def load_profile(path: str | Path) -> Profile:
    text = Path(path).read_text(encoding="utf-8")
    keywords: dict[str, list[str]] = {}
    for m in _LAYER_SECTION_RE.finditer(text):
        layer = m.group(1)
        end = text.find("### ", m.end())
        chunk = text[m.end(): end if end != -1 else len(text)]
        found: list[str] = []
        for line in chunk.splitlines():
            if line.strip().startswith("-"):
                tail = _BULLET_KW_RE.search(line)
                if tail:
                    for kw in re.split(r"[、，,/]", tail.group(1)):
                        kw = kw.strip()
                        if kw:
                            found.append(kw)
        keywords[layer] = found
    scale: dict[str, int] = {}
    for line in text.splitlines():
        m = _SCALE_ROW_RE.match(line)
        if m:
            for word in re.split(r"[、，,]", m.group(1)):
                word = word.strip()
                if word and not word.startswith("(") and not word.startswith("（"):
                    scale[word] = int(m.group(2))
    return Profile(keywords_by_layer=keywords, strength_scale=scale)

def _hits(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw in text]

def _nearby_strength(text: str, keyword: str, scale: dict[str, int]) -> tuple[str, int]:
    """Return (modifier, score) for the strongest modifier within ±10 chars of keyword."""
    best = ("", 0)
    for match in re.finditer(re.escape(keyword), text):
        start = max(0, match.start() - 10)
        end = min(len(text), match.end() + 10)
        window = text[start:end]
        for modifier, score in scale.items():
            if modifier in window and score > best[1]:
                best = (modifier, score)
    return best

def compute_diff(old: Document, new: Document, profile: Profile) -> DiffReport:
    items: list[DiffItem] = []
    old_text, new_text = old.raw_text, new.raw_text

    for layer in ("A1", "A2", "A3", "A4", "A5", "A6"):
        kws = profile.keywords_by_layer.get(layer, [])
        old_hits, new_hits = set(_hits(old_text, kws)), set(_hits(new_text, kws))
        for kw in new_hits - old_hits:
            items.append(DiffItem(layer=layer, change_type="added", old="", new=kw, note="新增表述"))
        for kw in old_hits - new_hits:
            items.append(DiffItem(layer=layer, change_type="removed", old=kw, new="", note="不再提及"))
        for kw in old_hits & new_hits:
            old_mod, old_score = _nearby_strength(old_text, kw, profile.strength_scale)
            new_mod, new_score = _nearby_strength(new_text, kw, profile.strength_scale)
            if new_score != old_score:
                items.append(DiffItem(
                    layer=layer,
                    change_type="modified",
                    old=f"{old_mod}{kw}" if old_mod else kw,
                    new=f"{new_mod}{kw}" if new_mod else kw,
                    note=f"强度 {old_score}→{new_score}",
                ))

    # A7 aggregation
    added_terms = [i.new for i in items if i.change_type == "added"]
    removed_terms = [i.old for i in items if i.change_type == "removed"]
    intensified = [i for i in items if i.change_type == "modified" and "→" in i.note]
    a7_note = f"新增 {len(added_terms)} 项；消失 {len(removed_terms)} 项；强度变化 {len(intensified)} 项"
    items.append(DiffItem(layer="A7", change_type="modified", old="", new="", note=a7_note))

    # Strength scores per layer (mean of all keyword nearby scores)
    strength: list[StrengthScore] = []
    for layer in ("A1", "A2", "A3", "A4", "A5", "A6"):
        kws = profile.keywords_by_layer.get(layer, [])
        old_scores = [_nearby_strength(old_text, k, profile.strength_scale)[1] for k in kws if k in old_text]
        new_scores = [_nearby_strength(new_text, k, profile.strength_scale)[1] for k in kws if k in new_text]
        strength.append(StrengthScore(
            dimension=f"{layer}_{'定调工具产业风险民生区域对外'[ (int(layer[1])-1)*2 : int(layer[1])*2 ]}",
            old=sum(old_scores)/len(old_scores) if old_scores else 0.0,
            new=sum(new_scores)/len(new_scores) if new_scores else 0.0,
        ))

    # Term freq across all layers' keywords
    term_freq: dict[str, dict[str, int]] = {}
    for layer, kws in profile.keywords_by_layer.items():
        for kw in kws:
            term_freq[kw] = {"old": old_text.count(kw), "new": new_text.count(kw)}

    return DiffReport(
        old_doc_title=old.title,
        new_doc_title=new.title,
        items=items,
        strength=strength,
        term_freq=term_freq,
    )
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_diff_engine.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/diff_engine.py tests/test_diff_engine.py
git commit -m "Add MECE diff engine for A1-A7 layer detection with profile-driven keywords"
```

---

## Task 7: Score Model (`scripts/score_model.py`) — term-freq CSV helper

**Rationale:** `diff_engine` already computes term_freq and strength; `score_model` exposes helper functions to reshape them into pandas DataFrames for the xlsx builder.

**Files:**
- Create: `scripts/score_model.py`
- Create: `tests/test_score_model.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_score_model.py
import pandas as pd
from scripts.models import DiffReport, StrengthScore
from scripts.score_model import top_n_term_freq, strength_to_dataframe

def test_top_n_term_freq_sorts_by_absolute_delta():
    tf = {
        "新质生产力": {"old": 0, "new": 12},
        "稳健": {"old": 8, "new": 7},
        "房地产": {"old": 5, "new": 3},
    }
    df = top_n_term_freq(tf, n=2)
    assert list(df["term"]) == ["新质生产力", "房地产"]
    assert df.iloc[0]["delta"] == 12

def test_strength_to_dataframe_has_6_rows():
    scores = [StrengthScore(f"A{i}_x", 1.0, 2.0) for i in range(1, 7)]
    df = strength_to_dataframe(scores)
    assert len(df) == 6
    assert list(df.columns) == ["dimension", "old", "new", "delta"]
    assert (df["delta"] == 1.0).all()
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_score_model.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/score_model.py`**

```python
import pandas as pd
from scripts.models import StrengthScore

def top_n_term_freq(term_freq: dict[str, dict[str, int]], n: int = 20) -> pd.DataFrame:
    rows = [
        {"term": term, "old": f["old"], "new": f["new"], "delta": f["new"] - f["old"]}
        for term, f in term_freq.items()
    ]
    df = pd.DataFrame(rows)
    df["abs_delta"] = df["delta"].abs()
    df = df.sort_values("abs_delta", ascending=False).head(n).drop(columns="abs_delta")
    return df.reset_index(drop=True)

def strength_to_dataframe(scores: list[StrengthScore]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"dimension": s.dimension, "old": s.old, "new": s.new, "delta": s.new - s.old} for s in scores]
    )
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_score_model.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/score_model.py tests/test_score_model.py
git commit -m "Add score_model helpers converting diff outputs to DataFrames"
```

---

## Task 8: Chart Builder (`scripts/build_charts.py`) — G1–G6

**Rationale:** Each G-function takes a `DiffReport` (or slice of it) + output path, writes a PNG. Chinese font fallback is critical on matplotlib.

**Files:**
- Create: `scripts/build_charts.py`
- Create: `tests/test_build_charts.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_build_charts.py
from scripts.models import DiffReport, DiffItem, StrengthScore
from scripts.build_charts import (
    build_g1_wordfreq_bar,
    build_g2_strength_radar,
    build_g3_config_matrix,
    build_g4_indicator_lines,
    build_g5_sector_sunburst,
    build_g6_flow_sankey,
)

def _sample_report():
    return DiffReport(
        old_doc_title="2023",
        new_doc_title="2024",
        items=[DiffItem(layer="A3", change_type="added", old="", new="新质生产力", note="")],
        strength=[StrengthScore(f"A{i}_x", 2.0, 3.0) for i in range(1, 7)],
        term_freq={"新质生产力": {"old": 0, "new": 12}, "稳健": {"old": 8, "new": 5}},
    )

def test_g1_wordfreq_bar_writes_png(tmp_path):
    out = tmp_path / "G1.png"
    build_g1_wordfreq_bar(_sample_report(), out)
    assert out.exists() and out.stat().st_size > 1000

def test_g2_strength_radar_writes_png(tmp_path):
    out = tmp_path / "G2.png"
    build_g2_strength_radar(_sample_report(), out)
    assert out.exists() and out.stat().st_size > 1000

def test_g3_config_matrix_writes_png(tmp_path):
    out = tmp_path / "G3.png"
    config = {"科技": ("超配", 0.9), "消费": ("标配", 0.6), "地产": ("低配", 0.3)}
    build_g3_config_matrix(config, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g4_indicator_lines_writes_png(tmp_path):
    out = tmp_path / "G4.png"
    series = {"GDP 目标": [5.5, 5.0, 5.0], "CPI 目标": [3.0, 3.0, 3.0]}
    years = [2022, 2023, 2024]
    build_g4_indicator_lines(series, years, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g5_sector_sunburst_writes_png(tmp_path):
    out = tmp_path / "G5.png"
    sectors = [
        {"parent": "", "label": "产业", "value": 10},
        {"parent": "产业", "label": "科技", "value": 4},
        {"parent": "产业", "label": "制造", "value": 3},
        {"parent": "产业", "label": "消费", "value": 3},
    ]
    build_g5_sector_sunburst(sectors, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g6_flow_sankey_writes_png(tmp_path):
    out = tmp_path / "G6.png"
    flows = [("新增", "新质生产力", 5), ("消失", "去产能", 3), ("升调", "房地产", 2)]
    build_g6_flow_sankey(flows, out)
    assert out.exists() and out.stat().st_size > 1000
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_build_charts.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/build_charts.py`**

```python
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import plotly.graph_objects as go

from scripts.models import DiffReport
from scripts.score_model import top_n_term_freq, strength_to_dataframe

# Chinese font setup: try PingFang SC, fall back to SimHei, else default
_CN_FONTS = ["PingFang SC", "Heiti TC", "SimHei", "Microsoft YaHei", "Arial Unicode MS"]
for f in _CN_FONTS:
    if any(f in fp.name for fp in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.edgecolor"] = "#333"

def build_g1_wordfreq_bar(report: DiffReport, out: Path, top_n: int = 20) -> None:
    df = top_n_term_freq(report.term_freq, n=top_n)
    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.35)))
    y = np.arange(len(df))
    ax.barh(y - 0.2, df["old"], height=0.4, color="#888", label=report.old_doc_title)
    ax.barh(y + 0.2, df["new"], height=0.4, color="#c00", label=report.new_doc_title)
    ax.set_yticks(y)
    ax.set_yticklabels(df["term"])
    ax.invert_yaxis()
    ax.set_xlabel("词频")
    ax.set_title("G1 关键词词频对比")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g2_strength_radar(report: DiffReport, out: Path) -> None:
    df = strength_to_dataframe(report.strength)
    categories = df["dimension"].tolist()
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist() + [0]
    old = df["old"].tolist() + [df["old"].iloc[0]]
    new = df["new"].tolist() + [df["new"].iloc[0]]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})
    ax.plot(angles, old, color="#888", label=report.old_doc_title)
    ax.fill(angles, old, color="#888", alpha=0.15)
    ax.plot(angles, new, color="#c00", label=report.new_doc_title)
    ax.fill(angles, new, color="#c00", alpha=0.2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 5)
    ax.set_title("G2 政策强度雷达")
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g3_config_matrix(config: dict[str, tuple[str, float]], out: Path) -> None:
    levels = ["超配", "标配", "低配"]
    level_idx = {lv: i for i, lv in enumerate(levels)}
    sectors = list(config.keys())
    grid = np.zeros((len(levels), len(sectors)))
    for j, sec in enumerate(sectors):
        level, conf = config[sec]
        grid[level_idx[level], j] = conf
    fig, ax = plt.subplots(figsize=(max(6, len(sectors) * 1.2), 3))
    im = ax.imshow(grid, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(levels)))
    ax.set_yticklabels(levels)
    ax.set_xticks(range(len(sectors)))
    ax.set_xticklabels(sectors, rotation=30, ha="right")
    for i in range(len(levels)):
        for j in range(len(sectors)):
            if grid[i, j] > 0:
                ax.text(j, i, f"{grid[i, j]:.1f}", ha="center", va="center", color="white" if grid[i, j] > 0.5 else "#333")
    ax.set_title("G3 行业配置矩阵 (置信度)")
    fig.colorbar(im, ax=ax, label="置信度")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g4_indicator_lines(series: dict[str, list[float]], years: list[int], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, values in series.items():
        ax.plot(years, values, marker="o", label=name)
    ax.set_xlabel("年份")
    ax.set_ylabel("目标值 (%)")
    ax.set_title("G4 关键指标历史曲线")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g5_sector_sunburst(sectors: list[dict], out: Path) -> None:
    labels = [s["label"] for s in sectors]
    parents = [s["parent"] for s in sectors]
    values = [s["value"] for s in sectors]
    fig = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total"))
    fig.update_layout(title="G5 产业地图", margin=dict(t=40, l=10, r=10, b=10))
    fig.write_image(str(out), width=900, height=700)

def build_g6_flow_sankey(flows: list[tuple[str, str, int]], out: Path) -> None:
    srcs = sorted({f[0] for f in flows})
    dsts = sorted({f[1] for f in flows})
    label = srcs + dsts
    idx = {lab: i for i, lab in enumerate(label)}
    fig = go.Figure(go.Sankey(
        node=dict(label=label, color="#c00"),
        link=dict(
            source=[idx[f[0]] for f in flows],
            target=[idx[f[1]] for f in flows],
            value=[f[2] for f in flows],
        ),
    ))
    fig.update_layout(title="G6 措辞流向图", margin=dict(t=40, l=10, r=10, b=10))
    fig.write_image(str(out), width=900, height=600)
```

- [ ] **Step 4: Install plotly image export deps if needed**

Run: `pip install kaleido` (plotly's PNG exporter).

- [ ] **Step 5: Run — expect pass**

Run: `pytest tests/test_build_charts.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_charts.py tests/test_build_charts.py
git commit -m "Add G1-G6 chart builders with Chinese font fallback"
```

---

## Task 9: Excel Builder (`scripts/build_xlsx.py`)

**Rationale:** Produce `data.xlsx` with 4 sheets from `DiffReport`.

**Files:**
- Create: `scripts/build_xlsx.py`
- Create: `tests/test_build_xlsx.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_build_xlsx.py
from openpyxl import load_workbook
from scripts.models import DiffReport, DiffItem, StrengthScore
from scripts.build_xlsx import build_xlsx

def _sample_report():
    return DiffReport(
        old_doc_title="2023",
        new_doc_title="2024",
        items=[
            DiffItem(layer="A1", change_type="modified", old="GDP 5.5%", new="GDP 5%", note="目标下调"),
            DiffItem(layer="A3", change_type="added", old="", new="新质生产力", note=""),
        ],
        strength=[StrengthScore(f"A{i}_x", 2.0, 3.0) for i in range(1, 7)],
        term_freq={"新质生产力": {"old": 0, "new": 12}, "房地产": {"old": 5, "new": 3}},
    )

def test_xlsx_has_four_sheets(tmp_path):
    out = tmp_path / "data.xlsx"
    build_xlsx(_sample_report(), out)
    wb = load_workbook(out)
    assert wb.sheetnames == ["指标对比", "词频统计", "政策强度", "差异清单"]

def test_diff_list_sheet_rows_match_report(tmp_path):
    report = _sample_report()
    out = tmp_path / "data.xlsx"
    build_xlsx(report, out)
    wb = load_workbook(out)
    ws = wb["差异清单"]
    # header + 2 items
    assert ws.max_row == len(report.items) + 1
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_build_xlsx.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/build_xlsx.py`**

```python
from pathlib import Path
from openpyxl import Workbook
from scripts.models import DiffReport
from scripts.score_model import top_n_term_freq, strength_to_dataframe

A1_QUANTITATIVE_KEYS = ("GDP", "国内生产总值", "赤字率", "CPI", "居民消费价格", "城镇新增就业")

def _write_df(ws, df) -> None:
    ws.append(list(df.columns))
    for _, row in df.iterrows():
        ws.append(list(row))

def build_xlsx(report: DiffReport, out: Path) -> None:
    wb = Workbook()

    # Sheet 1: 指标对比 — rows from term_freq whose term is a quantitative key
    ws1 = wb.active
    ws1.title = "指标对比"
    ws1.append(["指标", f"旧版({report.old_doc_title})", f"新版({report.new_doc_title})", "差值"])
    for term, freq in report.term_freq.items():
        if any(k in term for k in A1_QUANTITATIVE_KEYS):
            ws1.append([term, freq["old"], freq["new"], freq["new"] - freq["old"]])

    # Sheet 2: 词频统计 — top-50
    ws2 = wb.create_sheet("词频统计")
    _write_df(ws2, top_n_term_freq(report.term_freq, n=50))

    # Sheet 3: 政策强度
    ws3 = wb.create_sheet("政策强度")
    _write_df(ws3, strength_to_dataframe(report.strength))

    # Sheet 4: 差异清单
    ws4 = wb.create_sheet("差异清单")
    ws4.append(["层级", "变化类型", "旧版表述", "新版表述", "备注"])
    for item in report.items:
        ws4.append([item.layer, item.change_type, item.old, item.new, item.note])

    wb.save(out)
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_build_xlsx.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_xlsx.py tests/test_build_xlsx.py
git commit -m "Add Excel builder producing 4-sheet data.xlsx from DiffReport"
```

---

## Task 10: Writing Style Guides (`assets/style_*.md`)

**Rationale:** Loaded by SKILL.md at runtime so Claude can write the article body in the selected style.

**Files:**
- Create: `assets/style_research.md`
- Create: `assets/style_media.md`
- Create: `assets/style_retail.md`

- [ ] **Step 1: Write `assets/style_research.md`**

```markdown
# Style: 投研派 (research)

Audience: institutional investors / sell-side analysts. Goal: rigorous, citable.

## Structure (strict)
1. **摘要** (≤200 字)：一句话结论 + 3 条核心判断
2. **结论** (市场风格 / 行业配置 / 交易节奏 三张表)
3. **分维度论证** (按 A1–A7 依次展开，每层先给结论再给证据)
4. **风险提示** (对结论的反向观点)
5. **附录**：差异清单表、关键词词频表

## Language
- 术语密度高（宏观、货币、财政、专项债、新质生产力…）
- 数据优先，段落常以数字开头
- 避免感情色彩；用"我们判断"而非"我觉得"
- 结论句带置信度（高/中/低）
```

- [ ] **Step 2: Write `assets/style_media.md`**

```markdown
# Style: 媒体派 (media, 《财经》深度)

Audience: educated general readers. Goal: narrative, interpretive, compelling.

## Structure (flexible)
1. **开篇场景** (100-300 字)：从一个具体细节/数字/场景切入
2. **深度解读** (分 3-5 个小标题推进，每个围绕一个核心观察)
3. **观点抛出** (作者立场清晰的判断段落)
4. **延展思考** (跳出当前报告看历史/国际对照)

## Language
- 叙事性，用连词推进 ("然而"、"值得注意的是"、"更深层的变化在于")
- 适度使用比喻
- 术语出现时做一句话解释
- 引用具体表述时带出处 ("2024 年报告原文：...")
```

- [ ] **Step 3: Write `assets/style_retail.md`**

```markdown
# Style: 投资派 (retail, 大白话版)

Audience: retail investors / general public. Goal: radically accessible, directly actionable.

## Structure (loose)
1. **一句话结论**
2. **掰开揉碎讲** (用日常类比解释政策，3-5 个点，每个 ≤200 字)
3. **划重点** (bullet 列表，每条一个简单结论)
4. **操作提示** (带免责声明)

## Language
- 短句，口语化 ("说白了"、"简单讲"、"举个例子")
- 避开术语，必须用时立刻解释："赤字率其实就是政府今年打算借多少钱占 GDP 的比"
- 可以用 emoji
- 数字尽量做类比（"5% 增速，相当于一个中等国家一年的总产出"）
```

- [ ] **Step 4: Commit**

```bash
git add assets/
git commit -m "Add 3 writing style guides (research/media/retail)"
```

---

## Task 11: Word Builder (`scripts/build_docx.py`)

**Rationale:** Assembles `report.docx` from (title, sections, tables). The sections — actual Chinese prose — are produced by Claude at runtime per the selected style guide and handed to this builder as a list of `(heading, paragraphs)` pairs. Builder stays deterministic.

**Files:**
- Create: `scripts/build_docx.py`
- Create: `tests/test_build_docx.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_build_docx.py
from docx import Document as DocxDocument
from scripts.build_docx import build_report

def test_build_report_writes_docx_with_headings(tmp_path):
    sections = [
        ("摘要", ["本文对比 2023 和 2024 政府工作报告。", "核心结论：GDP 目标下调，政策重点转向新质生产力。"]),
        ("结论", ["成长 > 价值；内需 > 外需；进攻 > 防守。"]),
    ]
    disclaimer = "本文仅供研究参考，不构成投资建议。"
    out = tmp_path / "report.docx"
    build_report(
        title="2024 vs 2023 政府工作报告分析",
        style="research",
        sections=sections,
        disclaimer=disclaimer,
        output_path=out,
    )
    assert out.exists()
    doc = DocxDocument(out)
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert "摘要" in headings
    assert "结论" in headings
    full = "\n".join(p.text for p in doc.paragraphs)
    assert disclaimer in full
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_build_docx.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/build_docx.py`**

```python
from pathlib import Path
from docx import Document
from docx.shared import Pt

def build_report(
    *,
    title: str,
    style: str,
    sections: list[tuple[str, list[str]]],
    disclaimer: str,
    output_path: Path,
) -> None:
    doc = Document()

    # Title
    doc.add_heading(title, level=0)
    doc.add_paragraph(f"风格：{style}").italic = True

    # Body
    for heading, paragraphs in sections:
        doc.add_heading(heading, level=1)
        for para in paragraphs:
            doc.add_paragraph(para)

    # Disclaimer at end
    doc.add_heading("免责声明", level=2)
    p = doc.add_paragraph(disclaimer)
    p.runs[0].font.size = Pt(9)

    doc.save(output_path)
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_build_docx.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_docx.py tests/test_build_docx.py
git commit -m "Add Word report assembler with heading/paragraph/disclaimer layout"
```

---

## Task 12: CLI Entry (`scripts/run.py`)

**Rationale:** One entry point that SKILL.md invokes with JSON config on stdin, orchestrates parse → diff → score → xlsx → charts. Article prose is NOT produced by this script — SKILL.md handles that (LLM step) and calls `build_docx` separately.

**Files:**
- Create: `scripts/run.py`
- Create: `tests/test_run.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_run.py
import json
from scripts.run import run_analysis

def test_run_analysis_produces_xlsx_and_charts(tmp_path, fixtures_dir):
    # Build two text docs in-place
    old_text = "2023 政府工作报告\n一、回顾\nGDP 增长 5.5%，积极稳妥化解房地产风险。"
    new_text = "2024 政府工作报告\n一、回顾\nGDP 增长 5% 左右，大力发展新质生产力，坚决防范房地产风险。"
    config = {
        "old": {"mode": "text", "content": old_text, "year": 2023},
        "new": {"mode": "text", "content": new_text, "year": 2024},
        "file_type": "govt_work_report",
        "profile_path": "references/profile_govt_work_report.md",
        "output_dir": str(tmp_path),
    }
    result = run_analysis(config)
    out = tmp_path
    assert (out / "data.xlsx").exists()
    assert (out / "charts" / "G1_词频对比.png").exists()
    assert (out / "charts" / "G2_政策强度雷达.png").exists()
    assert "diff_report" in result
    assert any(i["layer"] == "A7" for i in result["diff_report"]["items"])
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_run.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `scripts/run.py`**

```python
"""CLI entry. Called by SKILL.md.

Input (JSON via stdin or passed to run_analysis):
{
  "old": {"mode": "text|url|pdf|docx", "content"|"url"|"path": "...", "year": 2023},
  "new": {"mode": "...", ..., "year": 2024},
  "file_type": "govt_work_report",
  "profile_path": "references/profile_govt_work_report.md",
  "output_dir": "./output"
}

Returns dict with diff_report summary. Writes data.xlsx + charts/*.png.
"""

from __future__ import annotations
import json
import sys
from dataclasses import asdict
from pathlib import Path

from scripts.models import Document
from scripts.parse_input import parse_text, parse_pdf, parse_docx
from scripts.fetcher import fetch
from scripts.diff_engine import load_profile, compute_diff
from scripts.build_xlsx import build_xlsx
from scripts.build_charts import (
    build_g1_wordfreq_bar,
    build_g2_strength_radar,
    build_g6_flow_sankey,
)

def _load_doc(spec: dict, cache_dir: Path) -> Document:
    mode = spec["mode"]
    year = spec["year"]
    if mode == "text":
        return parse_text(spec["content"], year=year)
    if mode == "url":
        text = fetch(spec["url"], cache_dir=cache_dir)
        return parse_text(text, year=year, source_url=spec["url"])
    if mode == "pdf":
        return parse_pdf(Path(spec["path"]), year=year)
    if mode == "docx":
        return parse_docx(Path(spec["path"]), year=year)
    raise ValueError(f"unsupported mode: {mode}")

def run_analysis(config: dict) -> dict:
    out_dir = Path(config["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    cache_dir = Path(config.get("cache_dir", "cache"))

    old = _load_doc(config["old"], cache_dir)
    new = _load_doc(config["new"], cache_dir)
    profile = load_profile(config["profile_path"])
    report = compute_diff(old, new, profile)

    build_xlsx(report, out_dir / "data.xlsx")
    build_g1_wordfreq_bar(report, charts_dir / "G1_词频对比.png")
    build_g2_strength_radar(report, charts_dir / "G2_政策强度雷达.png")

    # G3, G4, G5 require LLM-derived inputs (allocation tree, indicator history,
    # sector hierarchy) — SKILL.md generates them after the article-writing step.
    # G6 sankey is purely structural; we can produce it from the diff items alone.
    flows: list[tuple[str, str, int]] = []
    for item in report.items:
        if item.change_type == "added" and item.new:
            flows.append(("新增", item.new, 1))
        elif item.change_type == "removed" and item.old:
            flows.append(("消失", item.old, 1))
        elif item.change_type == "modified" and "→" in item.note:
            flows.append(("升降调", item.new or item.old, 1))
    if flows:
        build_g6_flow_sankey(flows, charts_dir / "G6_措辞流向.png")

    return {
        "diff_report": asdict(report),
        "output_dir": str(out_dir),
        "charts_dir": str(charts_dir),
    }

def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: run.py <config.json>", file=sys.stderr)
        return 2
    config = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    result = run_analysis(config)
    print(json.dumps({"output_dir": result["output_dir"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_run.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/run.py tests/test_run.py
git commit -m "Add CLI entry orchestrating parse->diff->xlsx->charts"
```

---

## Task 13: SKILL.md (the skill itself)

**Rationale:** This is what Claude loads when triggered. Must cover: when to trigger, Mode A/B decision tree, how to invoke `run.py`, how to write the article per style, disclaimer.

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: Write `SKILL.md`**

````markdown
---
name: policy-diff-analyst
description: Comparative analysis of Chinese policy documents (政府工作报告 first; CEWC / 五年规划 / 三中全会 / 货政报告 later). Use whenever the user asks to compare two versions of a Chinese policy document, analyze policy shifts year-over-year, extract changes in wording/tone/priorities between 政府工作报告 versions, or auto-fetch + compare recent policy papers by intent (e.g. "对比最新两版政府工作报告", "近三年政策趋势"). Produces a Word analysis article + Excel data table + PNG chart folder.
---

# Policy Diff Analyst

Compare two (or N) versions of a Chinese policy document, produce:
1. `output/report.docx` — analysis article in one of 3 styles (research / media / retail)
2. `output/data.xlsx` — 4-sheet data table (indicators / term frequency / strength scores / diff list)
3. `output/charts/` — G1–G6 PNG charts

## When this skill triggers

Trigger on any of:
- User provides two versions of a Chinese policy document and asks for comparison
- User says "对比最新/近 N 年的 XX 政策文件" (Mode B auto-fetch)
- User mentions 政府工作报告 / 中央经济工作会议 / 五年规划 / 三中全会决定 / 货币政策执行报告 comparison
- User wants policy-driven investment analysis (风格判断 / 行业配置 / 交易节奏)

## v1 scope

Only `file_type=govt_work_report` is supported in v1. For other document types, tell the user they will be supported in later versions.

## Required inputs (identify from the user's prompt; ask if missing)

| Field | Mode A | Mode B | Default |
|-------|:------:|:------:|---------|
| new version | ✅ | — | — |
| old version | ✅ | — | — |
| intent description | — | ✅ | — |
| file_type | ✅ | ✅ | govt_work_report |
| N versions (Mode B only) | — | 2 | 2 |
| article_style | ✅ | ✅ | ask user; options: research / media / retail |
| output_dir | ❌ | ❌ | `./output` |

Do not assume. If any required field is missing, ask one focused question.

## Mode decision

- **Mode A** (explicit inputs): user supplies URLs, PDF/docx paths, or pasted text.
- **Mode B** (intent-driven): user describes intent like "最新两版" / "近三年趋势". You:
  1. Determine file_type, N, year range
  2. For each year, call `scripts/source_registry.get_sources(file_type, year)`
  3. **Display the URL list to the user and wait for confirmation** before fetching
  4. After confirmation, `scripts.run.run_analysis` handles fetch + parse via its `mode=url` branch
  5. Only URLs returned by `source_registry` are ever fetched — do not pass user-provided URLs into Mode B

## Workflow

### Step 1 — Parse intent, collect inputs
Ask missing questions. For Mode B, present URL list and get confirmation.

### Step 2 — Build config and invoke run.py
```json
{
  "old": {"mode": "text|url|pdf|docx", ...},
  "new": {"mode": "text|url|pdf|docx", ...},
  "file_type": "govt_work_report",
  "profile_path": "references/profile_govt_work_report.md",
  "output_dir": "./output"
}
```
Save to `/tmp/config.json`, then run:
```bash
python -m scripts.run /tmp/config.json
```
This produces `output/data.xlsx` and `output/charts/G1,G2,G4,G6 .png`.

### Step 3 — Read the DiffReport JSON from run.py stdout + xlsx
Open the diff report to understand A1–A7 layers.

### Step 4 — Write the article body (YOU, the LLM)
Load the style guide:
- `assets/style_research.md` for research
- `assets/style_media.md` for media
- `assets/style_retail.md` for retail

Follow the guide's structure and language rules. Cover:
- **C1 market style judgment** (成长/价值 · 内需/外需 · 进攻/防守)
- **C2 sector allocation** (超配/标配/低配 + sector list + confidence)
- **C3 trading rhythm** (expectation → landing → realization)
- Analysis of all A1–A7 layers with concrete diff items as evidence

Hand the result to `build_docx.build_report` as `sections: list[(heading, [paragraph_str, ...])]`.

### Step 5 — Produce G3 and G5 charts (LLM-derived data)
G3 config matrix and G5 sector sunburst depend on your C2 judgment. After writing the article:
- Build `config` dict for G3 from your C2 allocation
- Build `sectors` list for G5 from A3 industry hits
- Call `build_charts.build_g3_config_matrix` and `build_charts.build_g5_sector_sunburst`

### Step 6 — Assemble report.docx
```python
from scripts.build_docx import build_report
build_report(
    title="...",
    style="research",
    sections=[...],
    disclaimer="本文基于公开政策文件分析，仅供研究参考，不构成投资建议。",
    output_path="output/report.docx",
)
```

### Step 7 — Report back
Tell the user:
- Output directory path
- What files were produced
- One-paragraph summary of your core finding

## Constraints

- **Never** fetch URLs outside `source_registry.ALLOWED_DOMAINS`. The whitelist is hardcoded for a reason.
- **Always** ask user confirmation of Mode B URL list before fetching.
- **Always** include the disclaimer in the final report.
- Mode B max N = 5 versions.
- Article body: strictly follow the selected style guide — do not mix styles.

## Reference files

- `references/profile_govt_work_report.md` — layer keyword map + scoring anchors
- `references/source_whitelist.md` — human-readable domain whitelist
- `assets/style_*.md` — style guides (loaded per-invocation)
````

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "Add SKILL.md with Mode A/B workflow and style-guided article protocol"
```

---

## Task 14: Source Whitelist Doc + Eval Set

**Files:**
- Create: `references/source_whitelist.md`
- Create: `evals/evals.json`

- [ ] **Step 1: Write `references/source_whitelist.md`**

```markdown
# Source Whitelist (Mode B)

Mode B may only fetch from these domains. Hardcoded in `scripts/source_registry.py` — any change requires a code edit, not prompt configuration.

## Allowed domains

- `www.gov.cn` — 中国政府网 (Tier 1, official)
- `www.news.cn` — 新华社 (Tier 2, authoritative media)
- `www.people.com.cn` — 人民网 (Tier 2, authoritative media)
- `www.pbc.gov.cn` — 中国人民银行 (Tier 1 for 货政报告, future)

## Why hardcoded
1. Prevents prompt injection from redirecting fetcher to attacker-controlled domains
2. Keeps provenance of analyzed documents auditable
3. Forces maintenance accountability — new sources go through code review
```

- [ ] **Step 2: Write `evals/evals.json`**

```json
{
  "skill_name": "policy-diff-analyst",
  "evals": [
    {
      "id": 1,
      "prompt": "这是 2024 政府工作报告和 2023 政府工作报告的全文（附上），请用投研派风格做对比分析。",
      "expected_output": "output/report.docx 投研派结构 + data.xlsx 4 sheets + charts G1-G6",
      "files": ["tests/fixtures/gwr_2024.txt", "tests/fixtures/gwr_2023.txt"]
    },
    {
      "id": 2,
      "prompt": "把 2024 和 2023 的政府工作报告对比一下，写得像《财经》那种深度风格。",
      "expected_output": "media 风格报告",
      "files": ["tests/fixtures/gwr_2024.txt", "tests/fixtures/gwr_2023.txt"]
    },
    {
      "id": 3,
      "prompt": "政府工作报告对比（2024 vs 2023），给我写个大白话通俗版。",
      "expected_output": "retail 风格报告",
      "files": ["tests/fixtures/gwr_2024.txt", "tests/fixtures/gwr_2023.txt"]
    },
    {
      "id": 4,
      "prompt": "帮我对比最新两版政府工作报告。",
      "expected_output": "Mode B triggered; URL list presented for confirmation; research-style output",
      "files": []
    },
    {
      "id": 5,
      "prompt": "近三年政府工作报告的趋势分析，投资派风格。",
      "expected_output": "Mode B with N=3; trend-style report_trend.docx",
      "files": []
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add references/source_whitelist.md evals/evals.json
git commit -m "Add source whitelist doc and initial eval set (5 cases)"
```

---

## Task 15: Smoke Test + README Update

**Rationale:** Run the full stack end-to-end with fixture text once, and update README with usage.

**Files:**
- Create: `tests/test_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Write end-to-end smoke test**

```python
# tests/test_smoke.py
from scripts.run import run_analysis

def test_full_pipeline_from_text(tmp_path):
    old_text = (
        "2023 政府工作报告\n一、2022 年工作回顾\n"
        "国内生产总值 121 万亿元，增长 3%。"
        "稳健的货币政策灵活适度，积极稳妥化解房地产风险。\n"
        "二、2023 年工作\n今年发展主要预期目标是：国内生产总值增长 5% 左右。"
    )
    new_text = (
        "2024 政府工作报告\n一、2023 年工作回顾\n"
        "国内生产总值 126 万亿元，增长 5.2%。"
        "稳健的货币政策精准有力，大力发展新质生产力。\n"
        "二、2024 年工作\n今年发展主要预期目标是：国内生产总值增长 5% 左右。"
        "坚决防范化解房地产风险，加快推进新能源汽车产业发展。"
    )
    config = {
        "old": {"mode": "text", "content": old_text, "year": 2023},
        "new": {"mode": "text", "content": new_text, "year": 2024},
        "file_type": "govt_work_report",
        "profile_path": "references/profile_govt_work_report.md",
        "output_dir": str(tmp_path),
    }
    result = run_analysis(config)
    assert (tmp_path / "data.xlsx").exists()
    assert (tmp_path / "charts" / "G1_词频对比.png").exists()
    assert (tmp_path / "charts" / "G2_政策强度雷达.png").exists()
    # A7 summary item is always present
    layers = {i["layer"] for i in result["diff_report"]["items"]}
    assert "A7" in layers
    # Added: 新质生产力 (in A3), 新能源 (in A3)
    added_news = [i["new"] for i in result["diff_report"]["items"] if i["change_type"] == "added"]
    assert any("新质生产力" in t for t in added_news)
```

- [ ] **Step 2: Run — expect pass**

Run: `pytest tests/test_smoke.py -v`
Expected: 1 passed.

- [ ] **Step 3: Update README.md**

Replace the existing README with:

```markdown
# policy-diff-analyst

Claude Code skill for comparative analysis of Chinese policy documents.

## What it does
- Compares two (or N up to 5) versions of a Chinese policy document
- Produces: Word article (投研派 / 媒体派 / 投资派 三选一) + Excel data table + G1-G6 PNG charts
- v1: 政府工作报告; later: 中央经济工作会议 / 五年规划 / 三中全会 / 货政报告 / 部委专项

## Modes
- **Mode A**: user supplies two documents (URL / PDF / .docx / pasted text)
- **Mode B**: user says "对比最新/近 N 年 XX 政策", skill auto-fetches from whitelisted sources

## Install

```bash
pip install -e ".[dev]"
```

## Usage

Via Claude Code: trigger the skill by asking to compare two policy documents. Manually via CLI:

```bash
python -m scripts.run config.json
```

See `SKILL.md` for the full Mode A/B protocol and `docs/superpowers/specs/` for the design spec.

## Development

```bash
pytest                  # run all tests
pytest tests/test_smoke.py -v   # end-to-end smoke
```
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_smoke.py README.md
git commit -m "Add end-to-end smoke test and expand README with usage"
```

---

## Post-Implementation Checklist

After all tasks complete, before handing to skill-creator for evals:

- [ ] `pytest` passes (all tests green)
- [ ] `python -m scripts.run` with a valid config.json produces expected outputs
- [ ] `SKILL.md` renders correctly and describes Mode A/B clearly
- [ ] `references/profile_govt_work_report.md` keyword list is consistent with `diff_engine.load_profile` parser
- [ ] `.gitignore` excludes `cache/`, `output/`, `__pycache__/`
- [ ] `evals/evals.json` has 5 cases
- [ ] Update `references/source_whitelist.md` with any new sources discovered during implementation
- [ ] Tag `v0.1.0` once smoke test passes end-to-end
