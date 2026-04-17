# policy-diff-analyst

Claude Code / Codex skill for comparative analysis of Chinese policy documents.

Automatically extracts document structure, compares keyword usage, scores policy intensity shifts, and tracks multi-year trends. Produces a Word analysis article + Excel data table + PNG charts.

## Supported document types

| file_type | Document | Profile |
|---|---|---|
| `govt_work_report` | 政府工作报告 | 7 layers, 62 keywords |
| `cewc` | 中央经济工作会议 | 7 layers, 91 keywords |
| `five_year_plan` | 五年规划纲要 | 8 layers, 105 keywords |
| `third_plenum` | 三中全会决定 | 7 layers, 84 keywords |
| `monetary_policy_report` | 货币政策执行报告 | 6 layers, 106 keywords |

## Features

- **Structure outline diff** — extract multi-level headings (一、/（一）/1.) and compare section ordering between versions
- **MECE keyword diff** — profile-driven keyword detection across policy layers (A1-A8)
- **Strength scoring** — 0-5 scale intensity assessment with modifier detection (大力/坚决/积极/稳妥…)
- **Temporal tracking** — N-year keyword trajectory classification (sustained / emerging / revived / fading / dropped)
- **Annotated docx** — red-highlighted new document with inline change annotations
- **Excel data table** — 4-sheet workbook (indicators / term frequency / strength scores / diff list)
- **6 chart types** — G1 word frequency bar, G2 strength radar, G3 config matrix, G4 indicator timeline, G5 sector sunburst, G6 wording flow sankey

## Install for Claude Code

```bash
# Clone into your personal skills directory
git clone https://github.com/carykwok/policy-diff-analyst.git ~/.claude/skills/policy-diff-analyst

# Install Python dependencies
cd ~/.claude/skills/policy-diff-analyst
pip install -e ".[dev]"
```

Claude Code auto-detects the skill immediately — no restart needed.

**Alternative: project-level install** (only available in one project):
```bash
git clone https://github.com/carykwok/policy-diff-analyst.git .claude/skills/policy-diff-analyst
```

## Install for Codex CLI

```bash
# Clone into your Codex skills directory
git clone https://github.com/carykwok/policy-diff-analyst.git ~/.codex/skills/policy-diff-analyst

# Install Python dependencies
cd ~/.codex/skills/policy-diff-analyst
pip install -e ".[dev]"
```

Restart Codex CLI after installation. The skill appears in `/skills` list.

## Usage

The skill triggers automatically when you ask Claude / Codex to compare policy documents:

```
对比 2023 和 2024 年政府工作报告
```
```
分析近三年中央经济工作会议的政策变化趋势
```
```
Compare these two monetary policy reports [attach files]
```

### Modes

- **Mode A** (explicit inputs): supply URLs, PDF/docx paths, or paste text directly
- **Mode B** (intent-driven): describe what you want (e.g. "最新两版政府工作报告"), skill auto-fetches from whitelisted government sources

### Output

```
output/
├── report.docx              # Analysis article (research / media / retail style)
├── annotated_new.docx       # Red-highlighted new document with structure diff
├── data.xlsx                # 4-sheet data workbook
└── charts/
    ├── G1_词频对比.png
    ├── G2_政策强度雷达.png
    └── G6_措辞流向.png
```

### CLI (standalone)

```bash
python -m scripts.run config.json
```

See `SKILL.md` for the full workflow protocol.

## Development

```bash
pip install -e ".[dev]"
pytest                          # 57 tests
pytest tests/test_smoke.py -v   # end-to-end smoke test
```

## License

MIT
