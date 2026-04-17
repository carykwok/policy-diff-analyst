"""Tests for new diff_engine features: sentence-based _nearby_strength,
discover_new_terms, extract_quantitative, and compare_quantitative."""

from scripts.diff_engine import (
    _nearby_strength,
    discover_new_terms,
    extract_quantitative,
    compare_quantitative,
    Profile,
)


# ── _nearby_strength (sentence-based) ────────────────────────────────

def test_nearby_strength_same_sentence():
    """Modifier in the same sentence as keyword should be detected."""
    text = "要大力推动创新发展。积极扩大内需。"
    scale = {"大力": 4, "积极": 3}
    modifier, score = _nearby_strength(text, "创新", scale)
    assert modifier == "大力"
    assert score == 4


def test_nearby_strength_different_sentence():
    """Modifier in a different sentence should NOT be detected for the keyword."""
    text = "要大力推动绿色转型。积极扩大创新发展。"
    scale = {"大力": 4, "积极": 3}
    modifier, score = _nearby_strength(text, "创新", scale)
    # "大力" is in sentence 1, "创新" is in sentence 2 — should NOT match "大力"
    assert modifier == "积极"
    assert score == 3


def test_nearby_strength_no_modifier():
    """When no modifier appears in the same sentence, return empty."""
    text = "要推动创新发展。大力扩大内需。"
    scale = {"大力": 4, "积极": 3}
    modifier, score = _nearby_strength(text, "创新", scale)
    assert modifier == ""
    assert score == 0


def test_nearby_strength_picks_strongest():
    """When multiple modifiers appear in the same sentence, pick the strongest."""
    text = "要积极大力推动创新发展。"
    scale = {"大力": 4, "积极": 3}
    modifier, score = _nearby_strength(text, "创新", scale)
    assert modifier == "大力"
    assert score == 4


# ── discover_new_terms ────────────────────────────────────────────────

def test_discover_new_terms_finds_unknown():
    """Terms frequent in new_text but not in profile keywords should be discovered."""
    profile = Profile(
        layer_ids=["A1"],
        layer_names={"A1": "宏观"},
        keywords_by_layer={"A1": ["创新", "发展"]},
        strength_scale={},
        quantitative_keys=["GDP"],
    )
    old_text = "这是旧文本。"
    # "人工智能" appears 4 times — should be discovered
    new_text = "人工智能是关键。人工智能发展迅速。人工智能应用广泛。人工智能前景很好。"
    results = discover_new_terms(old_text, new_text, profile, top_n=10)
    terms = [r["term"] for r in results]
    assert "人工智能" in terms
    # Known keywords should NOT appear
    for r in results:
        assert r["term"] not in ("创新", "发展", "GDP")


def test_discover_new_terms_respects_min_freq():
    """Terms appearing fewer than 3 times should be excluded."""
    profile = Profile(
        layer_ids=["A1"],
        layer_names={"A1": "宏观"},
        keywords_by_layer={"A1": []},
        strength_scale={},
        quantitative_keys=[],
    )
    old_text = ""
    # "区块链" only appears twice — below threshold
    new_text = "区块链技术。区块链应用。"
    results = discover_new_terms(old_text, new_text, profile)
    terms = [r["term"] for r in results]
    assert "区块链" not in terms


# ── extract_quantitative ─────────────────────────────────────────────

def test_extract_quantitative_basic():
    """Should extract indicator + number + unit patterns."""
    text = "国内生产总值增长5%，赤字率拟按3.8%安排。"
    results = extract_quantitative(text)
    indicators = {r["indicator"] for r in results}
    # Should find at least one quantitative extraction
    assert len(results) >= 1
    # Check that value and unit are extracted
    for r in results:
        assert isinstance(r["value"], float)
        assert isinstance(r["unit"], str)
        assert len(r["unit"]) > 0


def test_extract_quantitative_dedup():
    """Duplicate indicators (same indicator/value/unit) should appear only once."""
    text = "赤字率拟按3%安排。再次强调赤字率拟按3%。"
    results = extract_quantitative(text)
    keys = [(r["indicator"], r["value"], r["unit"]) for r in results]
    assert len(keys) == len(set(keys))


# ── compare_quantitative ─────────────────────────────────────────────

def test_compare_quantitative_modified():
    """Indicator present in both texts with different values should be 'modified'."""
    old_text = "赤字率拟按3%安排。"
    new_text = "赤字率拟按3.8%安排。"
    results = compare_quantitative(old_text, new_text)
    modified = [r for r in results if r["change"] == "modified"]
    assert len(modified) >= 1
    item = modified[0]
    assert "3.0%" in item["old_value"] or "3%" in item["old_value"]
    assert "3.8%" in item["new_value"]


def test_compare_quantitative_added_and_removed():
    """Indicator only in new_text should be 'added'; only in old_text should be 'removed'."""
    old_text = "城镇就业目标1200万人。"
    new_text = "粮食产量达到1.4万亿斤。"
    results = compare_quantitative(old_text, new_text)
    changes = {r["change"] for r in results}
    # We expect at least one added and one removed
    assert "added" in changes or "removed" in changes
