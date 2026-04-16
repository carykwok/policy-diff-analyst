from scripts.models import DiffReport, DiffItem, StrengthScore
from scripts.build_charts import (
    build_g1_wordfreq_bar,
    build_g2_strength_radar,
    build_g3_config_matrix,
    build_g4_indicator_lines,
    build_g5_sector_sunburst,
    build_g6_flow_sankey,
)

def _sample_report():
    return DiffReport(
        old_doc_title="2023",
        new_doc_title="2024",
        items=[DiffItem(layer="A3", change_type="added", old="", new="新质生产力", note="")],
        strength=[StrengthScore(f"A{i}_x", 2.0, 3.0) for i in range(1, 7)],
        term_freq={"新质生产力": {"old": 0, "new": 12}, "稳健": {"old": 8, "new": 5}},
    )

def test_g1_wordfreq_bar_writes_png(tmp_path):
    out = tmp_path / "G1.png"
    build_g1_wordfreq_bar(_sample_report(), out)
    assert out.exists() and out.stat().st_size > 1000

def test_g2_strength_radar_writes_png(tmp_path):
    out = tmp_path / "G2.png"
    build_g2_strength_radar(_sample_report(), out)
    assert out.exists() and out.stat().st_size > 1000

def test_g3_config_matrix_writes_png(tmp_path):
    out = tmp_path / "G3.png"
    config = {"科技": ("超配", 0.9), "消费": ("标配", 0.6), "地产": ("低配", 0.3)}
    build_g3_config_matrix(config, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g4_indicator_lines_writes_png(tmp_path):
    out = tmp_path / "G4.png"
    series = {"GDP 目标": [5.5, 5.0, 5.0], "CPI 目标": [3.0, 3.0, 3.0]}
    years = [2022, 2023, 2024]
    build_g4_indicator_lines(series, years, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g5_sector_sunburst_writes_png(tmp_path):
    out = tmp_path / "G5.png"
    sectors = [
        {"parent": "", "label": "产业", "value": 10},
        {"parent": "产业", "label": "科技", "value": 4},
        {"parent": "产业", "label": "制造", "value": 3},
        {"parent": "产业", "label": "消费", "value": 3},
    ]
    build_g5_sector_sunburst(sectors, out)
    assert out.exists() and out.stat().st_size > 1000

def test_g6_flow_sankey_writes_png(tmp_path):
    out = tmp_path / "G6.png"
    flows = [("新增", "新质生产力", 5), ("消失", "去产能", 3), ("升调", "房地产", 2)]
    build_g6_flow_sankey(flows, out)
    assert out.exists() and out.stat().st_size > 1000
