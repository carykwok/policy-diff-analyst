from scripts.models import Document, Section
from scripts.diff_engine import load_profile, compute_diff

PROFILE_PATH = "references/profile_govt_work_report.md"

def _doc(year, text):
    return Document(
        title=f"{year} 政府工作报告",
        year=year,
        file_type="govt_work_report",
        source_url=None,
        sections=[Section(heading="一、回顾", body=text)],
        raw_text=text,
    )

def test_load_profile_returns_layer_keywords():
    profile = load_profile(PROFILE_PATH)
    assert "新质生产力" in profile.keywords_by_layer["A3"]
    assert "房地产" in profile.keywords_by_layer["A4"]
    assert profile.strength_scale["大力"] == 4

def test_compute_diff_detects_added_and_removed_terms():
    old = _doc(2023, "GDP 增长 5.5%，积极稳妥化解房地产风险。")
    new = _doc(2024, "GDP 增长 5% 左右，大力发展新质生产力，坚决防范房地产风险。")
    profile = load_profile(PROFILE_PATH)
    report = compute_diff(old, new, profile)

    layers_seen = {item.layer for item in report.items}
    # A3 gets 'added' items (新质生产力); A4 intensity shifts (积极稳妥→坚决 around 房地产)
    assert "A3" in layers_seen
    assert "A4" in layers_seen
    assert "A7" in layers_seen       # aggregate summary always present

    added = [i for i in report.items if i.change_type == "added"]
    assert any("新质生产力" in i.new for i in added)

    a4_items = [i for i in report.items if i.layer == "A4" and i.change_type == "modified"]
    assert any("强度" in i.note for i in a4_items)
