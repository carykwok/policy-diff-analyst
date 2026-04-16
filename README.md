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
