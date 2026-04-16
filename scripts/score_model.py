import pandas as pd
from scripts.models import StrengthScore

def top_n_term_freq(term_freq: dict[str, dict[str, int]], n: int = 20) -> pd.DataFrame:
    rows = [
        {"term": term, "old": f["old"], "new": f["new"], "delta": f["new"] - f["old"]}
        for term, f in term_freq.items()
    ]
    df = pd.DataFrame(rows)
    df["abs_delta"] = df["delta"].abs()
    df = df.sort_values("abs_delta", ascending=False).head(n).drop(columns="abs_delta")
    return df.reset_index(drop=True)

def strength_to_dataframe(scores: list[StrengthScore]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"dimension": s.dimension, "old": s.old, "new": s.new, "delta": s.new - s.old} for s in scores]
    )
