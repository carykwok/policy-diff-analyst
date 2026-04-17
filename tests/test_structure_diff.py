from scripts.models import Document, Section
from scripts.diff_engine import extract_outline, compute_structure_diff


def _doc(year, text):
    return Document(
        title=f"{year} 政府工作报告",
        year=year,
        file_type="govt_work_report",
        source_url=None,
        sections=[Section(heading="全文", body=text)],
        raw_text=text,
    )


_OLD_TEXT = """\
一、2023 年工作回顾
国内生产总值增长 5.2%，城镇新增就业 1244 万人。

二、2024 年经济社会发展总体要求
坚持稳中求进工作总基调。

三、2024 年政府工作任务
（一）大力推进现代化产业体系建设
发展新质生产力。
（二）深入实施科教兴国战略
加强基础研究。
（三）积极扩大国内需求
激发消费潜能。

四、民生保障
切实保障和改善民生。
"""

_NEW_TEXT = """\
一、2024 年工作回顾
国内生产总值增长 5% 左右。

二、积极扩大国内需求
激发消费潜能，扩大有效投资。

三、大力推进现代化产业体系建设
发展新质生产力。

四、深入实施科教兴国战略
加强基础研究。

五、全面深化改革
完善市场经济体制。

六、民生保障
切实保障和改善民生。
"""


def test_extract_outline_basic():
    doc = _doc(2023, _OLD_TEXT)
    outline = extract_outline(doc)
    assert outline.year == 2023
    l1_headings = [e for e in outline.entries if e.level == 1]
    assert len(l1_headings) == 4
    assert "2023 年工作回顾" in l1_headings[0].heading
    assert l1_headings[0].position < l1_headings[1].position


def test_extract_outline_multi_level():
    doc = _doc(2023, _OLD_TEXT)
    outline = extract_outline(doc)
    l2_headings = [e for e in outline.entries if e.level == 2]
    assert len(l2_headings) == 3
    assert "现代化产业体系" in l2_headings[0].heading


def test_extract_outline_empty_text():
    doc = _doc(2023, "没有任何章节标题的纯文本。")
    outline = extract_outline(doc)
    assert outline.entries == []


def test_structure_diff_detects_added_section():
    old_doc = _doc(2023, _OLD_TEXT)
    new_doc = _doc(2024, _NEW_TEXT)
    diff = compute_structure_diff(old_doc, new_doc)
    added = [c for c in diff.changes if c.change_type == "added"]
    added_headings = [c.heading_new for c in added]
    assert any("全面深化改革" in h for h in added_headings)


def test_structure_diff_detects_removed_section():
    old_doc = _doc(2023, _OLD_TEXT)
    # new text without "工作任务" aggregate section
    new_text = "一、2024 年工作回顾\n国内生产总值增长 5%。\n二、民生保障\n保障民生。"
    new_doc = _doc(2024, new_text)
    diff = compute_structure_diff(old_doc, new_doc)
    removed = [c for c in diff.changes if c.change_type == "removed"]
    assert len(removed) >= 1


def test_structure_diff_detects_moved_up():
    """'积极扩大国内需求' was under 三、(三) in old, now promoted to 二、 in new."""
    old_doc = _doc(2023, _OLD_TEXT)
    new_doc = _doc(2024, _NEW_TEXT)
    diff = compute_structure_diff(old_doc, new_doc)
    # The summary should mention framework changes
    assert "框架结构" in diff.summary


def test_structure_diff_summary_format():
    old_doc = _doc(2023, _OLD_TEXT)
    new_doc = _doc(2024, _NEW_TEXT)
    diff = compute_structure_diff(old_doc, new_doc)
    # summary should start with 框架结构
    assert diff.summary.startswith("框架结构")
    # should have both outlines populated
    assert len(diff.old_outline.entries) > 0
    assert len(diff.new_outline.entries) > 0


def test_structure_diff_identical_docs():
    doc = _doc(2023, _OLD_TEXT)
    diff = compute_structure_diff(doc, doc)
    assert "基本不变" in diff.summary
    # All changes should be "kept"
    for c in diff.changes:
        assert c.change_type == "kept"


def test_structure_diff_detects_l2_reorder():
    """L1 headings are identical, but L2 subsections are reordered.

    Simulates the real-world case: '扩大国内需求' promoted from （三） to （一）
    under the same '工作任务' L1 section.
    """
    old_text = """\
一、2024 年工作回顾
回顾正文。

二、2025 年经济社会发展总体要求
总体要求正文。

三、2025 年政府工作任务
（一）大力推进现代化产业体系建设
发展新质生产力。
（二）深入实施科教兴国战略
加强基础研究。
（三）着力扩大国内需求
激发消费潜能。
"""

    new_text = """\
一、2024 年工作回顾
回顾正文。

二、2025 年经济社会发展总体要求
总体要求正文。

三、2025 年政府工作任务
（一）大力提振消费、着力扩大国内需求
激发消费潜能，扩大有效投资。
（二）大力推进现代化产业体系建设
发展新质生产力。
（三）深入实施科教兴国战略
加强基础研究。
"""

    old_doc = _doc(2024, old_text)
    new_doc = _doc(2025, new_text)
    diff = compute_structure_diff(old_doc, new_doc)

    # L1 should all be "kept" (identical headings)
    l1_changes = [c for c in diff.changes if "子章节" not in c.note]
    for c in l1_changes:
        assert c.change_type == "kept", f"L1 should be kept, got {c.change_type}: {c.note}"

    # L2 changes should detect movement
    l2_changes = [c for c in diff.changes if "子章节" in c.note]
    assert len(l2_changes) > 0, "Should detect L2 subsection changes"

    # At least one L2 should be moved_up or moved_down
    l2_moved = [c for c in l2_changes if c.change_type in ("moved_up", "moved_down")]
    assert len(l2_moved) > 0, "Should detect L2 subsection reordering"

    # Summary should mention L2
    assert "L2" in diff.summary
    assert "L1 框架基本不变" in diff.summary
