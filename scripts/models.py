from dataclasses import dataclass
from typing import Literal

@dataclass
class Section:
    heading: str
    body: str

@dataclass
class Document:
    title: str
    year: int
    file_type: str
    source_url: str | None
    sections: list[Section]
    raw_text: str

ChangeType = Literal["added", "removed", "modified", "kept"]

@dataclass
class DiffItem:
    layer: str               # "A1" .. "A7"
    change_type: ChangeType
    old: str
    new: str
    note: str

@dataclass
class StrengthScore:
    dimension: str           # "A1_定调" | "A2_工具" | ... | "A6_区域对外"
    old: float               # 0.0–5.0
    new: float

@dataclass
class DiffReport:
    old_doc_title: str
    new_doc_title: str
    items: list[DiffItem]
    strength: list[StrengthScore]
    term_freq: dict[str, dict[str, int]]   # term -> {"old": n, "new": m}

@dataclass
class TemporalKeyword:
    keyword: str
    layer: str
    years_present: list[int]               # [2020, 2021, 2023] — present in these years
    years_absent: list[int]                 # [2022] — absent
    strength_by_year: dict[int, float]      # {2020: 3.0, 2021: 4.0, ...}
    status: str                             # "sustained" | "emerging" | "revived" | "fading" | "dropped"

@dataclass
class TemporalReport:
    doc_titles: list[str]                   # ordered by year
    years: list[int]
    keywords: list[TemporalKeyword]
    pairwise_reports: list[DiffReport]      # consecutive year pairs
