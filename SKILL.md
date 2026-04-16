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
