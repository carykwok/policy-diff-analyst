# Policy Diff Analyst — Codex Adapter

## Overview

This agent compares two versions of a Chinese policy document and produces:
1. `output/analysis_brief.json` — structured diff data for LLM analysis
2. `output/data.xlsx` — 4-sheet quantitative data
3. `output/charts/` — visualization PNGs
4. `output/report.docx` — final analysis article (LLM-generated)
5. `output/annotated_new.docx` — new document with red highlights

## Setup

```bash
cd /path/to/policy-diff-analyst
pip install -e .
```

## Workflow

### Step 1: Run the diff engine

Given two documents (text files, PDFs, or URLs), run:

```bash
pda compare --old path/to/old.txt --new path/to/new.txt \
    --old-year 2024 --new-year 2025 \
    --file-type govt_work_report \
    --output ./output
```

Or with a config JSON:

```bash
pda compare --config config.json
```

This produces `output/analysis_brief.json` + `output/data.xlsx` + `output/charts/` + `output/annotated_new.docx`.

### Step 2: Write the analysis article

Read the following files:
- `output/analysis_brief.json` — the structured data to analyze
- `prompts/analysis_prompt.md` — the analysis instructions
- `references/analysis_framework.md` — the 12-chapter methodology
- `assets/style_{research|media|retail}.md` — the chosen style guide

Follow the 9-point analysis requirements in `prompts/analysis_prompt.md`. Output a JSON with `sections`, `g3_config`, and `g5_sectors`.

### Step 3: Generate the Word report

```python
import json
from scripts.build_docx import build_report
from scripts.build_charts import build_g3_config_matrix

# Load your analysis output
analysis = json.loads(open("your_analysis_output.json").read())

# Build report
build_report(
    title="2025年政府工作报告解读",
    style="research",
    sections=analysis["sections"],
    disclaimer=analysis["disclaimer"],
    output_path="output/report.docx",
)

# Build G3 chart
build_g3_config_matrix(analysis["g3_config"], "output/charts/G3_行业配置矩阵.png")
```

## Supported file_types

| file_type | Document | Profile |
|-----------|----------|---------|
| `govt_work_report` | 政府工作报告 | `references/profile_govt_work_report.md` |
| `cewc` | 中央经济工作会议 | `references/profile_cewc.md` |
| `five_year_plan` | 五年规划纲要 | `references/profile_five_year_plan.md` |
| `third_plenum` | 三中全会决定 | `references/profile_third_plenum.md` |
| `monetary_policy_report` | 货币政策执行报告 | `references/profile_monetary_policy_report.md` |

## Key Constraints

- Never fetch URLs outside the allowed domains in `scripts/source_registry.py`
- Always include the disclaimer in the final report
- Do not use emoji characters in the article (python-docx encoding issue)
- Each analysis point must follow: 是什么→为什么→所以呢 (what→why→so what)
