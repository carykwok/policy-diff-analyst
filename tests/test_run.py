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
