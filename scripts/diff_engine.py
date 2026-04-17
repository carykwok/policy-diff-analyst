import re
from dataclasses import dataclass
from pathlib import Path
from scripts.models import (
    Document, DiffItem, DiffReport, StrengthScore,
    TemporalKeyword, TemporalReport,
    OutlineEntry, StructureOutline, StructureChange, StructureDiff,
)

@dataclass
class Profile:
    layer_ids: list[str]                         # ["A1", "A2", ...] — from profile md
    layer_names: dict[str, str]                  # {"A1": "宏观定调", ...}
    keywords_by_layer: dict[str, list[str]]      # "A1" -> [kw, ...]
    strength_scale: dict[str, int]               # "大力" -> 4
    quantitative_keys: list[str]                 # ["GDP", "赤字率", ...]

_LAYER_SET_RE = re.compile(r"^- (A\d+)\s+(.+)$", re.MULTILINE)
_LAYER_SECTION_RE = re.compile(r"^### (A\d+)\s+(.+)$", re.MULTILINE)
_BULLET_KW_RE = re.compile(r"[：:]\s*(.+)$")
_SCALE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d+)\s*\|")

def load_profile(path: str | Path) -> Profile:
    text = Path(path).read_text(encoding="utf-8")

    # Parse ## Layer set
    layer_ids: list[str] = []
    layer_names: dict[str, str] = {}
    layer_set_start = text.find("## Layer set")
    if layer_set_start != -1:
        next_h2 = text.find("\n## ", layer_set_start + 1)
        layer_set_chunk = text[layer_set_start: next_h2 if next_h2 != -1 else len(text)]
        for m in _LAYER_SET_RE.finditer(layer_set_chunk):
            layer_ids.append(m.group(1))
            layer_names[m.group(1)] = m.group(2).strip()

    # Parse ### layer keyword sections
    keywords: dict[str, list[str]] = {}
    for m in _LAYER_SECTION_RE.finditer(text):
        layer = m.group(1)
        end = text.find("### ", m.end())
        next_h2 = text.find("\n## ", m.end())
        boundaries = [b for b in [end, next_h2] if b != -1]
        stop = min(boundaries) if boundaries else len(text)
        chunk = text[m.end(): stop]
        found: list[str] = []
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                body = stripped.lstrip("-").strip()
                tail = _BULLET_KW_RE.search(body)
                kw_str = tail.group(1) if tail else body
                for kw in re.split(r"[、，,/]", kw_str):
                    kw = kw.strip()
                    if kw:
                        found.append(kw)
        keywords[layer] = found

    # Fallback: if no ## Layer set, infer from keyword sections
    if not layer_ids:
        layer_ids = sorted(keywords.keys())
        for lid in layer_ids:
            layer_names[lid] = lid

    # Parse ## Quantitative keys
    quantitative_keys: list[str] = []
    qk_start = text.find("## Quantitative keys")
    if qk_start != -1:
        next_h2 = text.find("\n## ", qk_start + 1)
        qk_chunk = text[qk_start: next_h2 if next_h2 != -1 else len(text)]
        for line in qk_chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                body = stripped.lstrip("-").strip()
                for kw in re.split(r"[、，,/]", body):
                    kw = kw.strip()
                    if kw:
                        quantitative_keys.append(kw)

    # Parse strength scale table
    scale: dict[str, int] = {}
    for line in text.splitlines():
        m = _SCALE_ROW_RE.match(line)
        if m:
            for word in re.split(r"[、，,]", m.group(1)):
                word = word.strip()
                if word and not word.startswith("(") and not word.startswith("（"):
                    scale[word] = int(m.group(2))

    return Profile(
        layer_ids=layer_ids,
        layer_names=layer_names,
        keywords_by_layer=keywords,
        strength_scale=scale,
        quantitative_keys=quantitative_keys,
    )

def _hits(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw in text]

def _nearby_strength(text: str, keyword: str, scale: dict[str, int]) -> tuple[str, int]:
    """Return (modifier, score) for the strongest modifier within ±10 chars of keyword."""
    best = ("", 0)
    for match in re.finditer(re.escape(keyword), text):
        start = max(0, match.start() - 10)
        end = min(len(text), match.end() + 10)
        window = text[start:end]
        for modifier, score in scale.items():
            if modifier in window and score > best[1]:
                best = (modifier, score)
    return best

def compute_diff(old: Document, new: Document, profile: Profile) -> DiffReport:
    items: list[DiffItem] = []
    old_text, new_text = old.raw_text, new.raw_text

    # Determine which layer is the aggregation layer (conventionally the last one
    # whose keyword map section says "横切层" or has no keywords — or simply the
    # last layer_id if its keywords are empty).
    agg_layer = None
    for lid in reversed(profile.layer_ids):
        if not profile.keywords_by_layer.get(lid):
            agg_layer = lid
            break

    for layer in profile.layer_ids:
        if layer == agg_layer:
            continue
        kws = profile.keywords_by_layer.get(layer, [])
        old_hits, new_hits = set(_hits(old_text, kws)), set(_hits(new_text, kws))
        for kw in new_hits - old_hits:
            items.append(DiffItem(layer=layer, change_type="added", old="", new=kw, note="新增表述"))
        for kw in old_hits - new_hits:
            items.append(DiffItem(layer=layer, change_type="removed", old=kw, new="", note="不再提及"))
        for kw in old_hits & new_hits:
            old_mod, old_score = _nearby_strength(old_text, kw, profile.strength_scale)
            new_mod, new_score = _nearby_strength(new_text, kw, profile.strength_scale)
            if new_score != old_score:
                items.append(DiffItem(
                    layer=layer,
                    change_type="modified",
                    old=f"{old_mod}{kw}" if old_mod else kw,
                    new=f"{new_mod}{kw}" if new_mod else kw,
                    note=f"强度 {old_score}→{new_score}",
                ))

    if agg_layer:
        added_terms = [i.new for i in items if i.change_type == "added"]
        removed_terms = [i.old for i in items if i.change_type == "removed"]
        intensified = [i for i in items if i.change_type == "modified"]
        agg_note = f"新增 {len(added_terms)} 项；消失 {len(removed_terms)} 项；强度变化 {len(intensified)} 项"
        items.append(DiffItem(layer=agg_layer, change_type="modified", old="", new="", note=agg_note))

    strength: list[StrengthScore] = []
    for layer in profile.layer_ids:
        if layer == agg_layer:
            continue
        kws = profile.keywords_by_layer.get(layer, [])
        old_scores = [_nearby_strength(old_text, k, profile.strength_scale)[1] for k in kws if k in old_text]
        new_scores = [_nearby_strength(new_text, k, profile.strength_scale)[1] for k in kws if k in new_text]
        strength.append(StrengthScore(
            dimension=f"{layer}_{profile.layer_names.get(layer, layer)}",
            old=sum(old_scores)/len(old_scores) if old_scores else 0.0,
            new=sum(new_scores)/len(new_scores) if new_scores else 0.0,
        ))

    # Term freq across all layers' keywords
    term_freq: dict[str, dict[str, int]] = {}
    for layer, kws in profile.keywords_by_layer.items():
        for kw in kws:
            term_freq[kw] = {"old": old_text.count(kw), "new": new_text.count(kw)}

    return DiffReport(
        old_doc_title=old.title,
        new_doc_title=new.title,
        items=items,
        strength=strength,
        term_freq=term_freq,
    )


def compute_temporal_diff(docs: list[Document], profile: Profile) -> TemporalReport:
    """Compare N documents (sorted by year) and track keyword trajectories.

    For each keyword in the profile, records which years it appeared,
    its strength score per year, and classifies the trajectory:
      - sustained: present in all years
      - emerging: absent early, present in recent years
      - revived: disappeared then came back
      - fading: strength declining over recent years
      - dropped: present early, absent in most recent year
    """
    docs = sorted(docs, key=lambda d: d.year)
    years = [d.year for d in docs]

    # Detect aggregation layer
    agg_layer = None
    for lid in reversed(profile.layer_ids):
        if not profile.keywords_by_layer.get(lid):
            agg_layer = lid
            break

    # Build per-keyword temporal data
    all_kws: list[tuple[str, str]] = []  # (keyword, layer)
    for layer in profile.layer_ids:
        if layer == agg_layer:
            continue
        for kw in profile.keywords_by_layer.get(layer, []):
            all_kws.append((kw, layer))

    temporal_keywords: list[TemporalKeyword] = []
    for kw, layer in all_kws:
        present = [d.year for d in docs if kw in d.raw_text]
        absent = [y for y in years if y not in present]
        strength_by_year: dict[int, float] = {}
        for d in docs:
            if kw in d.raw_text:
                _, score = _nearby_strength(d.raw_text, kw, profile.strength_scale)
                strength_by_year[d.year] = float(score)

        if not present:
            continue  # keyword never appears, skip

        # Classify trajectory
        if set(present) == set(years):
            # Check if fading (strength declining over last 2+ years)
            recent_scores = [strength_by_year[y] for y in years[-2:] if y in strength_by_year]
            if len(recent_scores) == 2 and recent_scores[-1] < recent_scores[-2]:
                status = "fading"
            else:
                status = "sustained"
        elif years[-1] not in present:
            status = "dropped"
        elif years[0] not in present and years[-1] in present:
            # Check for revival (gap in the middle)
            if any(y not in present for y in years[1:-1]) and any(y in present for y in years[:len(years)//2+1]):
                status = "revived"
            else:
                status = "emerging"
        else:
            # Present in first and last but gaps in middle
            status = "revived"

        temporal_keywords.append(TemporalKeyword(
            keyword=kw, layer=layer,
            years_present=present, years_absent=absent,
            strength_by_year=strength_by_year, status=status,
        ))

    # Build consecutive pairwise reports
    pairwise: list[DiffReport] = []
    for i in range(len(docs) - 1):
        pairwise.append(compute_diff(docs[i], docs[i + 1], profile))

    return TemporalReport(
        doc_titles=[d.title for d in docs],
        years=years,
        keywords=temporal_keywords,
        pairwise_reports=pairwise,
    )


# ── Structure outline & diff ──────────────────────────────────────────

# Level 1: 一、二、三、…  Level 2: （一）（二）…  Level 3: 1. 2. 3. …
_L1_RE = re.compile(r"^([一二三四五六七八九十百]+)、(.+)", re.MULTILINE)
_L2_RE = re.compile(r"^（([一二三四五六七八九十百]+)）\s*(.+)", re.MULTILINE)
_L3_RE = re.compile(r"^(\d+)[.、．]\s*(.+)", re.MULTILINE)


def extract_outline(doc: Document) -> StructureOutline:
    """Extract a multi-level heading outline from a Document."""
    entries: list[OutlineEntry] = []
    text = doc.raw_text

    headings: list[tuple[int, str, int]] = []  # (level, heading, char_offset)
    for m in _L1_RE.finditer(text):
        headings.append((1, m.group(0).strip(), m.start()))
    for m in _L2_RE.finditer(text):
        headings.append((2, m.group(0).strip(), m.start()))
    for m in _L3_RE.finditer(text):
        full = m.group(0).strip()
        # Skip very short matches (likely numbered lists in body text)
        if len(full) > 4:
            headings.append((3, full, m.start()))

    headings.sort(key=lambda h: h[2])

    for i, (level, heading, offset) in enumerate(headings):
        next_offset = headings[i + 1][2] if i + 1 < len(headings) else len(text)
        body_len = next_offset - offset
        entries.append(OutlineEntry(
            level=level, heading=heading, position=i, char_count=body_len,
        ))

    return StructureOutline(title=doc.title, year=doc.year, entries=entries)


def _normalize_heading(h: str) -> str:
    """Strip numbering prefix to get the topic core for matching."""
    # Remove "一、" / "（一）" / "1." prefix
    h = re.sub(r"^[一二三四五六七八九十百]+、\s*", "", h)
    h = re.sub(r"^（[一二三四五六七八九十百]+）\s*", "", h)
    h = re.sub(r"^\d+[.、．]\s*", "", h)
    return h.strip()


def compute_structure_diff(old_doc: Document, new_doc: Document) -> StructureDiff:
    """Compare the structural outlines of two documents.

    Detects: sections moved up/down (priority change), added/removed sections,
    renamed sections (same position, different wording).
    """
    old_outline = extract_outline(old_doc)
    new_outline = extract_outline(new_doc)

    # Work with level-1 headings for the primary structure comparison
    old_l1 = [(e.heading, e.position) for e in old_outline.entries if e.level == 1]
    new_l1 = [(e.heading, e.position) for e in new_outline.entries if e.level == 1]

    old_topics = {_normalize_heading(h): (h, pos) for h, pos in old_l1}
    new_topics = {_normalize_heading(h): (h, pos) for h, pos in new_l1}

    changes: list[StructureChange] = []

    # Match by normalized heading
    matched_old: set[str] = set()
    matched_new: set[str] = set()

    for topic in old_topics:
        if topic in new_topics:
            old_h, old_pos = old_topics[topic]
            new_h, new_pos = new_topics[topic]
            matched_old.add(topic)
            matched_new.add(topic)

            if old_h != new_h:
                changes.append(StructureChange(
                    heading_old=old_h, heading_new=new_h,
                    change_type="renamed",
                    old_position=old_pos, new_position=new_pos,
                    note=f"措辞调整：{old_h} → {new_h}",
                ))
            elif old_pos != new_pos:
                direction = "moved_up" if new_pos < old_pos else "moved_down"
                delta = abs(new_pos - old_pos)
                changes.append(StructureChange(
                    heading_old=old_h, heading_new=new_h,
                    change_type=direction,
                    old_position=old_pos, new_position=new_pos,
                    note=f"位置{'前移' if direction == 'moved_up' else '后移'} {delta} 位（优先级{'升' if direction == 'moved_up' else '降'}）",
                ))
            else:
                changes.append(StructureChange(
                    heading_old=old_h, heading_new=new_h,
                    change_type="kept",
                    old_position=old_pos, new_position=new_pos,
                    note="位置不变",
                ))

    # Fuzzy match remaining by substring overlap for renamed sections
    unmatched_old = {t: old_topics[t] for t in old_topics if t not in matched_old}
    unmatched_new = {t: new_topics[t] for t in new_topics if t not in matched_new}

    fuzzy_matched: set[str] = set()
    for ot, (oh, opos) in unmatched_old.items():
        best_score = 0
        best_nt = None
        for nt, (nh, npos) in unmatched_new.items():
            if nt in fuzzy_matched:
                continue
            # Simple overlap: count shared characters
            shared = sum(1 for c in ot if c in nt)
            score = shared / max(len(ot), len(nt), 1)
            if score > best_score and score > 0.4:
                best_score = score
                best_nt = nt
        if best_nt:
            nh, npos = unmatched_new[best_nt]
            fuzzy_matched.add(best_nt)
            matched_old.add(ot)
            matched_new.add(best_nt)
            changes.append(StructureChange(
                heading_old=oh, heading_new=nh,
                change_type="renamed",
                old_position=opos, new_position=npos,
                note=f"章节重组/更名：{oh} → {nh}",
            ))

    # Remaining unmatched = added/removed
    for topic in old_topics:
        if topic not in matched_old:
            h, pos = old_topics[topic]
            changes.append(StructureChange(
                heading_old=h, heading_new="",
                change_type="removed",
                old_position=pos, new_position=None,
                note=f"章节删除：{h}",
            ))

    for topic in new_topics:
        if topic not in matched_new:
            h, pos = new_topics[topic]
            changes.append(StructureChange(
                heading_old="", heading_new=h,
                change_type="added",
                old_position=None, new_position=pos,
                note=f"新增章节：{h}",
            ))

    # Sort by new_position (or old_position for removed)
    changes.sort(key=lambda c: c.new_position if c.new_position is not None else (c.old_position or 0))

    # Build summary
    moved = [c for c in changes if c.change_type in ("moved_up", "moved_down")]
    added = [c for c in changes if c.change_type == "added"]
    removed = [c for c in changes if c.change_type == "removed"]
    renamed = [c for c in changes if c.change_type == "renamed"]
    parts: list[str] = []
    if added:
        parts.append(f"新增 {len(added)} 个章节")
    if removed:
        parts.append(f"删除 {len(removed)} 个章节")
    if moved:
        up = [c for c in moved if c.change_type == "moved_up"]
        down = [c for c in moved if c.change_type == "moved_down"]
        if up:
            parts.append(f"{len(up)} 个章节前移（优先级提升）")
        if down:
            parts.append(f"{len(down)} 个章节后移")
    if renamed:
        parts.append(f"{len(renamed)} 个章节更名/重组")
    summary = "框架结构变动：" + "；".join(parts) if parts else "框架结构基本不变"

    return StructureDiff(
        old_outline=old_outline,
        new_outline=new_outline,
        changes=changes,
        summary=summary,
    )
