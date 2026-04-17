from scripts.models import Document, Section
from scripts.diff_engine import load_profile, compute_diff, Profile

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

def test_load_profile_parses_layer_set():
    profile = load_profile(PROFILE_PATH)
    assert profile.layer_ids == ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
    assert profile.layer_names["A1"] == "宏观定调"
    assert profile.layer_names["A6"] == "区域对外"

def test_load_profile_parses_quantitative_keys():
    profile = load_profile(PROFILE_PATH)
    assert "GDP" in profile.quantitative_keys
    assert "赤字率" in profile.quantitative_keys

def test_compute_diff_detects_added_and_removed_terms():
    old = _doc(2023, "GDP 增长 5.5%，积极稳妥化解房地产风险。")
    new = _doc(2024, "GDP 增长 5% 左右，大力发展新质生产力，坚决防范房地产风险。")
    profile = load_profile(PROFILE_PATH)
    report = compute_diff(old, new, profile)

    layers_seen = {item.layer for item in report.items}
    assert "A3" in layers_seen
    assert "A4" in layers_seen
    assert "A7" in layers_seen

    added = [i for i in report.items if i.change_type == "added"]
    assert any("新质生产力" in i.new for i in added)

    a4_items = [i for i in report.items if i.layer == "A4" and i.change_type == "modified"]
    assert any("强度" in i.note for i in a4_items)

def test_profile_drives_layer_set():
    mini = Profile(
        layer_ids=["X1", "X2"],
        layer_names={"X1": "经济", "X2": "金融"},
        keywords_by_layer={"X1": ["GDP"], "X2": ["利率"]},
        strength_scale={"大力": 4},
        quantitative_keys=["GDP"],
    )
    old = _doc(2023, "GDP 增长 5%，大力提升利率传导效率。")
    new = _doc(2024, "GDP 增长 5% 左右。")
    report = compute_diff(old, new, mini)
    dims = [s.dimension for s in report.strength]
    assert dims == ["X1_经济", "X2_金融"]
    assert len(report.strength) == 2

def test_load_cewc_profile():
    profile = load_profile("references/profile_cewc.md")
    assert "A1" in profile.layer_ids
    assert profile.layer_names["A4"] == "风险底线"
    assert "保交楼" in profile.keywords_by_layer["A4"]

def test_load_monetary_policy_profile():
    profile = load_profile("references/profile_monetary_policy_report.md")
    assert len(profile.layer_ids) == 6
    assert "A7" not in profile.layer_ids
    assert "LPR" in profile.quantitative_keys
