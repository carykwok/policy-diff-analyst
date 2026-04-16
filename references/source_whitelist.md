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
