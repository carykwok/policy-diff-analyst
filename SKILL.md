---
name: policy-diff-analyst
description: Comparative analysis of Chinese policy documents (政府工作报告 / 中央经济工作会议 / 五年规划纲要 / 三中全会决定 / 货币政策执行报告). Use whenever the user asks to compare two versions of a Chinese policy document, analyze policy shifts year-over-year, extract changes in wording/tone/priorities, or auto-fetch + compare recent policy papers by intent (e.g. "对比最新两版政府工作报告", "近三年经济工作会议趋势", "十四五 vs 十三五"). Produces a Word analysis article + Excel data table + PNG chart folder.
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

## Supported file_types

| file_type | 文档类型 | profile 文件 |
|---|---|---|
| `govt_work_report` | 政府工作报告 | `references/profile_govt_work_report.md` |
| `cewc` | 中央经济工作会议 | `references/profile_cewc.md` |
| `five_year_plan` | 五年规划纲要 | `references/profile_five_year_plan.md` |
| `third_plenum` | 三中全会决定 | `references/profile_third_plenum.md` |
| `monetary_policy_report` | 货币政策执行报告 | `references/profile_monetary_policy_report.md` |

## Required inputs (identify from the user's prompt; ask if missing)

| Field | Mode A | Mode B | Default |
|-------|:------:|:------:|---------|
| new version | ✅ | — | — |
| old version | ✅ | — | — |
| intent description | — | ✅ | — |
| file_type | ✅ | ✅ | 必须指定 |
| N versions (Mode B only) | — | 2 | 2 |
| article_style | ✅ | ✅ | ask user; options: research / media / retail |
| output_dir | ❌ | ❌ | `./output` |

Do not assume. If any required field is missing, ask one focused question.

## Mode decision

- **Mode A** (explicit inputs): user supplies URLs, PDF/docx paths, or pasted text.
- **Mode B** (intent-driven): user describes intent like "最新两版" / "近三年趋势". You:
  1. Determine file_type, N, year range
  2. For each year, call `scripts/source_registry.get_sources(file_type, year)` to get template URLs
  3. Try template URLs first. If they 404, use `source_registry.get_search_hint(file_type, year)` with WebSearch to discover actual URLs
  4. Validate all discovered URLs with `source_registry.is_allowed(url)` — reject any URL outside the whitelist
  5. **Display the URL list to the user and wait for confirmation** before fetching
  6. After confirmation, fetch and parse. Only whitelisted URLs are ever fetched

## Workflow

### Step 0 — Structure outline & framework diff (auto-generated)
`run_analysis` automatically extracts the structure outline of both documents and compares them:
- Multi-level heading detection: L1 `一、` / L2 `（一）` / L3 `1.`
- **L1 + L2 two-level comparison**: L1 checks top-level section changes; L2 checks subsection reordering within matched L1 pairs (e.g. "消费" promoted from （三） to （一） under "工作任务")
- Section ordering comparison: detects moved_up / moved_down / added / removed / renamed
- Framework-level summary (e.g. "L1 框架基本不变；L2 子章节：消费从第3升至第1")

This appears as the **first section** in `annotated_new.docx` ("一、框架结构对比") and in the `structure_diff` key of the result JSON. Present this to the reader **before** keyword-level analysis — it gives the most direct framework-level orientation.

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
Open the diff report and understand:
- `structure_diff`: L1/L2 framework changes (priority signal)
- `diff_report`: keyword-level changes across all profile layers
- `quantitative_comparison`: numerical indicator changes
- `new_term_candidates`: high-frequency terms not in profile (for Step 11)

### Step 4 — Write the article body (YOU, the LLM)

**First, load the analysis methodology:**
- `references/analysis_framework.md` — 完整解读方法论（12 章）

**Key framework sections to internalize:**
- §一-§三：定调谱系 + 量化三步法 + 措辞四类信号
- §七：**文档类型差异化视角**——不同 file_type 的分析切入角度完全不同（如货政报告关注流动性措辞，政府工作报告关注量化目标）
- §八：**关键词→行业传导映射表**——政策关键词到 A 股板块的具体映射
- §九：**政策周期定位**——先判断当前处于稳增长/调结构/防风险/促发展哪个阶段
- §十：**弦外之音读取**——信心水平、紧迫度、政策语言翻译表
- §十一：**浅层 vs 深度分析实例**——必须达到"深度分析"示例的水平
- §十二：**预期差分析**——实际政策 vs 市场预期的偏差

**Then, load the style guide:**
- `assets/style_research.md` for research
- `assets/style_media.md` for media
- `assets/style_retail.md` for retail

**Analysis requirements (all styles must cover, depth varies by style):**

1. **政策周期定位**：先判断当前处于什么周期阶段（§九），这是整篇分析的底色
2. **框架概览**：从 `structure_diff` 提取 L1/L2 位置变化，呈现全局结构变动
3. **定调判断**：按 §一 的谱系，判断宏观/财政/货币三重定调组合，与上年纵向对比
4. **量化目标解读**：按 §二 的三步法（数字→设定逻辑→市场含义），解读核心指标变化
5. **TOP 10 核心差异深度解读**：每个按 §六.1 + §十一 的深度示例标准（差异项→信号解读→历史对标→传导推演→置信度），参考 §十 读取弦外之音
6. **行业传导**：用 §八 的映射表，从政策差异推演到具体板块
7. **C1 市场风格判断**（§四.3）+ **C2 行业配置**（§四.2 + §八）+ **C3 交易节奏**
8. **预期差分析**（§十二）：标注市场事前预期 vs 实际政策的偏差
9. **风险与反向观点**：对核心判断给出反面论证 + §十.4 的反面验证

**核心原则：每个差异项必须走完"是什么→为什么→所以呢"三步，裸列差异不是分析。参照 §十一 的深度分析示例——达不到该水平的分析不合格。**

Hand the result to `build_docx.build_report` as `sections: list[(heading, [paragraph_str, ...])]`.
The last section should be the appendix containing old and new document full text.

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

### Step 7 — Annotated docx (auto-generated)
`run_analysis` automatically produces `output/annotated_new.docx`:
- Keywords **added** in new version: red bold + grey `【新增·A3】` inline tag
- Keywords with **strength change**: red bold + grey `【强度 3→5】` inline tag
- Keywords **removed**: collected in a "本版不再提及的表述" section at end

No extra config needed — this is always produced alongside data.xlsx.

### Step 8 — Temporal diff (optional, N-year comparison)
If the user provides 3+ years of documents, add `extra_docs` to config:
```json
{
  "old": {"mode": "text", "content": "...", "year": 2022},
  "new": {"mode": "text", "content": "...", "year": 2024},
  "extra_docs": [
    {"mode": "text", "content": "...", "year": 2023}
  ],
  ...
}
```
This produces `temporal_report` in the result dict with:
- Per-keyword trajectory: `sustained` / `emerging` / `revived` / `fading` / `dropped`
- `strength_by_year`: keyword strength scores across all years
- `pairwise_reports`: consecutive year-pair DiffReports

Use the temporal data to narrate multi-year trends in the article (e.g. "新质生产力 emerged in 2024, absent in 2022-2023").

### Step 9 — Quantitative indicator comparison
`run_analysis` returns `quantitative_comparison` — a list of extracted numerical indicators (GDP targets, deficit ratios, bond issuance amounts, etc.) with old vs new values. Present these as a structured table in the article. Key signals: target changes (5%→5%), scale changes (3.9→4.4万亿), and newly introduced targets.

### Step 10 — Report back
Tell the user:
- Output directory path
- What files were produced (including annotated_new.docx with structure outline)
- **Structure framework changes first** (from `structure_diff.summary`, both L1 and L2)
- Quantitative indicator changes (key number shifts)
- Then one-paragraph summary of keyword-level core findings

### Step 11 — Profile self-expansion (auto-triggered)
After analysis, `run_analysis` returns `new_term_candidates` — a list of high-frequency terms found in the new document that are NOT in the current profile. Present these to the user:
> "以下高频词不在当前 profile 关键词库中，是否需要加入？"
> (table of term / new_freq / old_freq)

If the user confirms specific terms, append them to the appropriate layer in the profile `.md` file. This keeps the keyword library evolving with policy vocabulary.

### Step 12 — Self-evaluation (optional, recommended for quality iteration)
After completing the analysis article, perform a quality self-check:

**Layer 2 — Expert cross-reference:**
1. Use WebSearch: `"{year}年政府工作报告 解读 中金/中信/国君"` (or equivalent for other file_types)
2. Compare your core conclusions with expert commentary
3. Flag any signals experts caught that you missed, or signals you reported that experts didn't mention
4. Output a brief "分析质量自评" noting gaps and confidence level

**Layer 3 — Temporal self-correction (for N-year analyses):**
1. Check if previous year's `temporal_report` predictions held:
   - "emerging" keywords: did they persist? → precision check
   - "fading" keywords: did they actually drop? → recall check
2. Output prediction accuracy rate
3. Feed back into trajectory classification tuning

## Constraints

- **Never** fetch URLs outside `source_registry.ALLOWED_DOMAINS`. The whitelist is hardcoded for a reason.
- **Always** ask user confirmation of Mode B URL list before fetching.
- **Always** include the disclaimer in the final report.
- Mode B max N = 5 versions.
- Article body: strictly follow the selected style guide — do not mix styles.

## Reference files

- `references/profile_govt_work_report.md` — 政府工作报告 layer keyword map + scoring anchors
- `references/profile_cewc.md` — 中央经济工作会议 profile
- `references/profile_five_year_plan.md` — 五年规划纲要 profile
- `references/profile_third_plenum.md` — 三中全会决定 profile
- `references/profile_monetary_policy_report.md` — 货币政策执行报告 profile
- `references/source_whitelist.md` — human-readable domain whitelist
- `assets/style_*.md` — style guides (loaded per-invocation)
