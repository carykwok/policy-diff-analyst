from scripts.models import Document, Section
from scripts.diff_engine import load_profile, compute_temporal_diff, Profile

PROFILE_PATH = "references/profile_govt_work_report.md"

def _doc(year, text):
    return Document(
        title=f"{year} 政府工作报告",
        year=year,
        file_type="govt_work_report",
        source_url=None,
        sections=[Section(heading="全文", body=text)],
        raw_text=text,
    )

def test_temporal_diff_tracks_keyword_across_years():
    docs = [
        _doc(2022, "GDP 增长 5.5%，积极稳妥化解房地产风险。"),
        _doc(2023, "GDP 增长 5%，大力发展新质生产力，积极化解房地产风险。"),
        _doc(2024, "GDP 增长 5% 左右，坚决发展新质生产力，坚决防范房地产风险。"),
    ]
    profile = load_profile(PROFILE_PATH)
    report = compute_temporal_diff(docs, profile)

    assert report.years == [2022, 2023, 2024]
    assert len(report.pairwise_reports) == 2

    kw_map = {tk.keyword: tk for tk in report.keywords}
    assert "GDP" in kw_map or "国内生产总值" in kw_map

    # 新质生产力: absent in 2022, present in 2023+2024
    if "新质生产力" in kw_map:
        nz = kw_map["新质生产力"]
        assert 2022 not in nz.years_present
        assert 2023 in nz.years_present
        assert nz.status == "emerging"

    # 房地产: present in all years
    if "房地产" in kw_map:
        fd = kw_map["房地产"]
        assert fd.years_present == [2022, 2023, 2024]
        assert fd.status in ("sustained", "fading")


def test_temporal_diff_with_custom_profile():
    mini = Profile(
        layer_ids=["X1"],
        layer_names={"X1": "test"},
        keywords_by_layer={"X1": ["alpha", "beta"]},
        strength_scale={"大力": 4, "坚决": 5},
        quantitative_keys=[],
    )
    docs = [
        _doc(2022, "We have alpha here."),
        _doc(2023, "No keywords at all."),
        _doc(2024, "alpha is back, 大力 alpha."),
    ]
    report = compute_temporal_diff(docs, mini)
    kw_map = {tk.keyword: tk for tk in report.keywords}
    assert "alpha" in kw_map
    alpha = kw_map["alpha"]
    assert alpha.status == "revived"
    assert 2023 in alpha.years_absent
    assert alpha.strength_by_year.get(2024, 0) == 4  # 大力 nearby


def test_temporal_diff_detects_dropped():
    mini = Profile(
        layer_ids=["X1"],
        layer_names={"X1": "test"},
        keywords_by_layer={"X1": ["gamma"]},
        strength_scale={},
        quantitative_keys=[],
    )
    docs = [
        _doc(2022, "gamma is important"),
        _doc(2023, "gamma continues"),
        _doc(2024, "no more of that keyword"),
    ]
    report = compute_temporal_diff(docs, mini)
    kw_map = {tk.keyword: tk for tk in report.keywords}
    assert kw_map["gamma"].status == "dropped"
