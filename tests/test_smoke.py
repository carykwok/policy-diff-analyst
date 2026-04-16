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
