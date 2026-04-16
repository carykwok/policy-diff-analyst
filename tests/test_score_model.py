import pandas as pd
from scripts.models import DiffReport, StrengthScore
from scripts.score_model import top_n_term_freq, strength_to_dataframe

def test_top_n_term_freq_sorts_by_absolute_delta():
    tf = {
        "新质生产力": {"old": 0, "new": 12},
        "稳健": {"old": 8, "new": 7},
        "房地产": {"old": 5, "new": 3},
    }
    df = top_n_term_freq(tf, n=2)
    assert list(df["term"]) == ["新质生产力", "房地产"]
    assert df.iloc[0]["delta"] == 12

def test_strength_to_dataframe_has_6_rows():
    scores = [StrengthScore(f"A{i}_x", 1.0, 2.0) for i in range(1, 7)]
    df = strength_to_dataframe(scores)
    assert len(df) == 6
    assert list(df.columns) == ["dimension", "old", "new", "delta"]
    assert (df["delta"] == 1.0).all()
