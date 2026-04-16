import re
from dataclasses import dataclass
from pathlib import Path
from scripts.models import Document, DiffItem, DiffReport, StrengthScore

@dataclass
class Profile:
    keywords_by_layer: dict[str, list[str]]      # "A1" -> [kw, ...]
    strength_scale: dict[str, int]               # "大力" -> 4

_LAYER_SECTION_RE = re.compile(r"^### (A[1-7])\s+(.+)$", re.MULTILINE)
_BULLET_KW_RE = re.compile(r"[：:]\s*(.+)$")
_SCALE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d+)\s*\|")

_LAYER_NAMES = {
    "A1": "定调",
    "A2": "工具",
    "A3": "产业",
    "A4": "风险",
    "A5": "民生",
    "A6": "区域对外",
}

def load_profile(path: str | Path) -> Profile:
    text = Path(path).read_text(encoding="utf-8")
    keywords: dict[str, list[str]] = {}
    for m in _LAYER_SECTION_RE.finditer(text):
        layer = m.group(1)
        end = text.find("### ", m.end())
        chunk = text[m.end(): end if end != -1 else len(text)]
        found: list[str] = []
        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                # Strip leading "- " and an optional "label：" prefix before splitting.
                body = stripped.lstrip("-").strip()
                tail = _BULLET_KW_RE.search(body)
                kw_str = tail.group(1) if tail else body
                for kw in re.split(r"[、，,/]", kw_str):
                    kw = kw.strip()
                    if kw:
                        found.append(kw)
        keywords[layer] = found
    scale: dict[str, int] = {}
    for line in text.splitlines():
        m = _SCALE_ROW_RE.match(line)
        if m:
            for word in re.split(r"[、，,]", m.group(1)):
                word = word.strip()
                if word and not word.startswith("(") and not word.startswith("（"):
                    scale[word] = int(m.group(2))
    return Profile(keywords_by_layer=keywords, strength_scale=scale)

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

    for layer in ("A1", "A2", "A3", "A4", "A5", "A6"):
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

    # A7 aggregation
    added_terms = [i.new for i in items if i.change_type == "added"]
    removed_terms = [i.old for i in items if i.change_type == "removed"]
    intensified = [i for i in items if i.change_type == "modified" and "→" in i.note]
    a7_note = f"新增 {len(added_terms)} 项；消失 {len(removed_terms)} 项；强度变化 {len(intensified)} 项"
    items.append(DiffItem(layer="A7", change_type="modified", old="", new="", note=a7_note))

    # Strength scores per layer (mean of all keyword nearby scores)
    strength: list[StrengthScore] = []
    for layer in ("A1", "A2", "A3", "A4", "A5", "A6"):
        kws = profile.keywords_by_layer.get(layer, [])
        old_scores = [_nearby_strength(old_text, k, profile.strength_scale)[1] for k in kws if k in old_text]
        new_scores = [_nearby_strength(new_text, k, profile.strength_scale)[1] for k in kws if k in new_text]
        strength.append(StrengthScore(
            dimension=f"{layer}_{_LAYER_NAMES[layer]}",
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
