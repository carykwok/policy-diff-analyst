import re
from dataclasses import dataclass
from pathlib import Path
from scripts.models import Document, DiffItem, DiffReport, StrengthScore

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
