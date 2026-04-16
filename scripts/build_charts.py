from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import plotly.graph_objects as go

from scripts.models import DiffReport
from scripts.score_model import top_n_term_freq, strength_to_dataframe

# Chinese font setup: try PingFang SC, fall back to SimHei, else default
_CN_FONTS = ["PingFang SC", "Heiti TC", "SimHei", "Microsoft YaHei", "Arial Unicode MS"]
for f in _CN_FONTS:
    if any(f in fp.name for fp in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.edgecolor"] = "#333"

def build_g1_wordfreq_bar(report: DiffReport, out: Path, top_n: int = 20) -> None:
    df = top_n_term_freq(report.term_freq, n=top_n)
    fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.35)))
    y = np.arange(len(df))
    ax.barh(y - 0.2, df["old"], height=0.4, color="#888", label=report.old_doc_title)
    ax.barh(y + 0.2, df["new"], height=0.4, color="#c00", label=report.new_doc_title)
    ax.set_yticks(y)
    ax.set_yticklabels(df["term"])
    ax.invert_yaxis()
    ax.set_xlabel("词频")
    ax.set_title("G1 关键词词频对比")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g2_strength_radar(report: DiffReport, out: Path) -> None:
    df = strength_to_dataframe(report.strength)
    categories = df["dimension"].tolist()
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist() + [0]
    old = df["old"].tolist() + [df["old"].iloc[0]]
    new = df["new"].tolist() + [df["new"].iloc[0]]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})
    ax.plot(angles, old, color="#888", label=report.old_doc_title)
    ax.fill(angles, old, color="#888", alpha=0.15)
    ax.plot(angles, new, color="#c00", label=report.new_doc_title)
    ax.fill(angles, new, color="#c00", alpha=0.2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 5)
    ax.set_title("G2 政策强度雷达")
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g3_config_matrix(config: dict[str, tuple[str, float]], out: Path) -> None:
    levels = ["超配", "标配", "低配"]
    level_idx = {lv: i for i, lv in enumerate(levels)}
    sectors = list(config.keys())
    grid = np.zeros((len(levels), len(sectors)))
    for j, sec in enumerate(sectors):
        level, conf = config[sec]
        grid[level_idx[level], j] = conf
    fig, ax = plt.subplots(figsize=(max(6, len(sectors) * 1.2), 3))
    im = ax.imshow(grid, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(levels)))
    ax.set_yticklabels(levels)
    ax.set_xticks(range(len(sectors)))
    ax.set_xticklabels(sectors, rotation=30, ha="right")
    for i in range(len(levels)):
        for j in range(len(sectors)):
            if grid[i, j] > 0:
                ax.text(j, i, f"{grid[i, j]:.1f}", ha="center", va="center", color="white" if grid[i, j] > 0.5 else "#333")
    ax.set_title("G3 行业配置矩阵 (置信度)")
    fig.colorbar(im, ax=ax, label="置信度")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g4_indicator_lines(series: dict[str, list[float]], years: list[int], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, values in series.items():
        ax.plot(years, values, marker="o", label=name)
    ax.set_xlabel("年份")
    ax.set_ylabel("目标值 (%)")
    ax.set_title("G4 关键指标历史曲线")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)

def build_g5_sector_sunburst(sectors: list[dict], out: Path) -> None:
    labels = [s["label"] for s in sectors]
    parents = [s["parent"] for s in sectors]
    values = [s["value"] for s in sectors]
    fig = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total"))
    fig.update_layout(title="G5 产业地图", margin=dict(t=40, l=10, r=10, b=10))
    fig.write_image(str(out), width=900, height=700)

def build_g6_flow_sankey(flows: list[tuple[str, str, int]], out: Path) -> None:
    srcs = sorted({f[0] for f in flows})
    dsts = sorted({f[1] for f in flows})
    label = srcs + dsts
    idx = {lab: i for i, lab in enumerate(label)}
    fig = go.Figure(go.Sankey(
        node=dict(label=label, color="#c00"),
        link=dict(
            source=[idx[f[0]] for f in flows],
            target=[idx[f[1]] for f in flows],
            value=[f[2] for f in flows],
        ),
    ))
    fig.update_layout(title="G6 措辞流向图", margin=dict(t=40, l=10, r=10, b=10))
    fig.write_image(str(out), width=900, height=600)
