from scripts.models import Document, Section, DiffItem, DiffReport, StrengthScore

def test_document_basic_construction():
    doc = Document(
        title="2024 政府工作报告",
        year=2024,
        file_type="govt_work_report",
        source_url="https://www.gov.cn/...",
        sections=[Section(heading="一、2023年工作回顾", body="...")],
        raw_text="全文..."
    )
    assert doc.year == 2024
    assert doc.sections[0].heading == "一、2023年工作回顾"

def test_diff_item_layers():
    item = DiffItem(layer="A1", change_type="modified", old="GDP 5.5%", new="GDP 5.0%", note="目标下调")
    assert item.layer == "A1"
    assert item.change_type in ("added", "removed", "modified", "kept")

def test_strength_score_range():
    s = StrengthScore(dimension="A3_产业", old=3.0, new=4.0)
    assert 0 <= s.old <= 5 and 0 <= s.new <= 5

def test_diff_report_aggregate():
    report = DiffReport(
        old_doc_title="2023",
        new_doc_title="2024",
        items=[DiffItem(layer="A1", change_type="added", old="", new="新质生产力", note="")],
        strength=[StrengthScore(dimension="A3_产业", old=3.0, new=4.0)],
        term_freq={"新质生产力": {"old": 0, "new": 12}},
    )
    assert len(report.items) == 1
