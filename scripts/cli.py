"""CLI entry point for `pda` command.

Usage:
    pda compare --old old.txt --new new.txt --file-type govt_work_report [--output ./output]
    pda compare --config config.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build_config_from_args(args: argparse.Namespace) -> dict:
    """Build a run config dict from CLI arguments."""
    file_type = args.file_type
    profile_map = {
        "govt_work_report": "references/profile_govt_work_report.md",
        "cewc": "references/profile_cewc.md",
        "five_year_plan": "references/profile_five_year_plan.md",
        "third_plenum": "references/profile_third_plenum.md",
        "monetary_policy_report": "references/profile_monetary_policy_report.md",
    }
    profile_path = profile_map.get(file_type)
    if not profile_path:
        print(f"Error: unknown file_type '{file_type}'", file=sys.stderr)
        sys.exit(1)

    def _make_source(path_str: str, year: int) -> dict:
        p = Path(path_str)
        if p.suffix == ".pdf":
            return {"mode": "pdf", "path": str(p.resolve()), "year": year}
        elif p.suffix == ".docx":
            return {"mode": "docx", "path": str(p.resolve()), "year": year}
        elif path_str.startswith("http"):
            return {"mode": "url", "url": path_str, "year": year}
        else:
            return {"mode": "text", "content": p.read_text(encoding="utf-8"), "year": year}

    return {
        "old": _make_source(args.old, args.old_year),
        "new": _make_source(args.new, args.new_year),
        "file_type": file_type,
        "profile_path": profile_path,
        "output_dir": args.output,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pda",
        description="Policy Diff Analyst — compare Chinese policy documents",
    )
    sub = parser.add_subparsers(dest="command")

    # pda compare
    cmp = sub.add_parser("compare", help="Compare two policy documents")
    cmp.add_argument("--config", help="Path to config JSON (overrides other args)")
    cmp.add_argument("--old", help="Path or URL to old document")
    cmp.add_argument("--new", help="Path or URL to new document")
    cmp.add_argument("--old-year", type=int, default=2024, help="Year of old document")
    cmp.add_argument("--new-year", type=int, default=2025, help="Year of new document")
    cmp.add_argument(
        "--file-type",
        default="govt_work_report",
        choices=["govt_work_report", "cewc", "five_year_plan", "third_plenum", "monetary_policy_report"],
        help="Document type",
    )
    cmp.add_argument("--output", default="./output", help="Output directory")

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.command != "compare":
        parser.print_help()
        return 0

    # Build or load config
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    elif args.old and args.new:
        config = _build_config_from_args(args)
    else:
        cmp.print_help()
        return 1

    # Import here to avoid slow jieba loading for --help
    from scripts.run import run_analysis

    result = run_analysis(config)
    brief_path = Path(result["output_dir"]) / "analysis_brief.json"
    print(f"Done. Output directory: {result['output_dir']}")
    print(f"Analysis brief: {brief_path}")
    print(f"Data: {result['output_dir']}/data.xlsx")
    print(f"Charts: {result['charts_dir']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
