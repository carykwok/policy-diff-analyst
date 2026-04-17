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
from scripts.diff_engine import load_profile, compute_diff, compute_temporal_diff, compute_structure_diff
from scripts.build_xlsx import build_xlsx
from scripts.build_annotated_docx import build_annotated_docx
from scripts.build_charts import (
    build_g1_wordfreq_bar,
    build_g2_strength_radar,
    build_g6_flow_sankey,
)

def _load_doc(spec: dict, cache_dir: Path, file_type: str) -> Document:
    mode = spec["mode"]
    year = spec["year"]
    if mode == "text":
        return parse_text(spec["content"], year=year, file_type=file_type)
    if mode == "url":
        text = fetch(spec["url"], cache_dir=cache_dir)
        return parse_text(text, year=year, file_type=file_type, source_url=spec["url"])
    if mode == "pdf":
        return parse_pdf(Path(spec["path"]), year=year, file_type=file_type)
    if mode == "docx":
        return parse_docx(Path(spec["path"]), year=year, file_type=file_type)
    raise ValueError(f"unsupported mode: {mode}")

def run_analysis(config: dict) -> dict:
    out_dir = Path(config["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    cache_dir = Path(config.get("cache_dir", "cache"))

    file_type = config.get("file_type", "govt_work_report")
    old = _load_doc(config["old"], cache_dir, file_type)
    new = _load_doc(config["new"], cache_dir, file_type)
    profile = load_profile(config["profile_path"])

    # Structure outline & diff — framework-level view before keyword analysis
    structure_diff = compute_structure_diff(old, new)

    report = compute_diff(old, new, profile)

    build_xlsx(report, out_dir / "data.xlsx", profile=profile)
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

    # Annotated docx: new document with red highlights + grey notes + structure summary
    build_annotated_docx(new.raw_text, report, out_dir / "annotated_new.docx",
                         structure_diff=structure_diff)

    # Temporal diff if extra docs provided
    temporal_result = None
    extra_docs_specs = config.get("extra_docs", [])
    if extra_docs_specs:
        all_docs = [old, new]
        for spec in extra_docs_specs:
            all_docs.append(_load_doc(spec, cache_dir, file_type))
        temporal = compute_temporal_diff(all_docs, profile)
        temporal_result = asdict(temporal)

    return {
        "diff_report": asdict(report),
        "structure_diff": asdict(structure_diff),
        "temporal_report": temporal_result,
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
