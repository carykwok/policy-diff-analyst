# 政策文档对比分析指令（通用版）

本文件是平台无关的分析指令。任何 LLM（Claude、GPT-4、Gemini、开源模型）均可使用。

## 输入

你将收到一个 `analysis_brief.json`，包含以下字段：

| 字段 | 说明 |
|------|------|
| `metadata` | 新旧文档标题、年份、file_type |
| `structure_diff` | 框架结构变化（L1 章节 + L2 子章节的增删/移位/更名） |
| `top_changes` | 前 15 大关键词差异项（含层级、变化类型、强度变化） |
| `strength_scores` | 各维度政策强度评分（0-5 分，含新旧对比和 delta） |
| `quantitative_indicators` | 量化指标变化（GDP 目标、赤字率、专项债等） |
| `new_term_candidates` | 高频新词（不在关键词库中的新增术语） |

## 参考资料

分析前请加载以下文件（按需选择）：

- `references/analysis_framework.md` — 完整解读方法论（12 章），核心章节：
  - 一~三：定调谱系 + 量化三步法 + 措辞四类信号
  - 七：文档类型差异化视角
  - 八：关键词→行业传导映射表
  - 九：政策周期定位
  - 十：弦外之音读取
  - 十一：浅层 vs 深度分析实例
  - 十二：预期差分析
- `references/profile_{file_type}.md` — 对应文档类型的关键词 profile
- `assets/style_{style}.md` — 写作风格指南（research / media / retail 三选一）

## 分析要求（9 个必覆盖点）

无论什么风格，以下 9 点必须全部覆盖（深度随风格调整）：

### 1. 政策周期定位
判断当前处于稳增长 / 调结构 / 防风险 / 促发展的哪个阶段。这是整篇分析的底色。

### 2. 框架概览
从 `structure_diff` 提取 L1/L2 位置变化，呈现全局结构变动。章节顺序的调整往往比措辞变化更能反映战略优先级。

### 3. 定调判断
判断宏观 / 财政 / 货币三重定调组合，与上年纵向对比。参考 analysis_framework.md 第一章的定调谱系。

### 4. 量化目标解读
按"三步法"（数字→设定逻辑→市场含义）解读 `quantitative_indicators` 中的核心指标变化。

### 5. TOP 10 核心差异深度解读
从 `top_changes` 中选取最重要的 10 个差异项，每个必须走完：
- **是什么**：措辞具体变化
- **为什么**：背后的政策意图和经济背景
- **所以呢**：对市场/行业的传导影响

裸列差异不是分析。每个差异项需要：信号解读→历史对标→传导推演→置信度评估。

### 6. 行业传导
从政策差异推演到具体 A 股板块。参考 analysis_framework.md 第八章的关键词→行业映射表。

### 7. 投资含义
- **C1 市场风格判断**：成长 vs 价值，大盘 vs 小盘
- **C2 行业配置**：超配 / 标配 / 低配及理由
- **C3 交易节奏**：政策发力的时间窗口和节奏判断

### 8. 预期差分析
标注市场事前预期 vs 实际政策的偏差。超预期和低于预期的部分是交易机会所在。

### 9. 风险与反向观点
对核心判断给出反面论证。好的分析必须包含"如果我错了，可能是因为…"。

## 输出格式

返回一个 JSON 对象，包含：

```json
{
  "sections": [
    ["章节标题", ["段落1文本", "段落2文本", ...]],
    ["章节标题", ["段落1文本", ...]],
    ...
  ],
  "g3_config": {
    "行业名": {"rating": "超配|标配|低配", "confidence": "高|中|低", "catalyst": "催化剂说明"},
    ...
  },
  "g5_sectors": [
    {"sector": "行业名", "sub_sectors": ["子行业1", "子行业2"], "policy_signal": "政策信号"}
  ],
  "disclaimer": "本文基于公开政策文件分析，仅供研究参考，不构成投资建议。"
}
```

最后一个 section 应为附录，包含新旧文档原文全文。

## 质量标准

- 每个差异项必须走完"是什么→为什么→所以呢"三步
- 参照 analysis_framework.md 第十一章的深度分析示例——达不到该水平不合格
- 不要使用 emoji 字符（python-docx 无法编码 surrogate pairs），用文字标记代替（如 `[超配]`、`[标配]`、`[低配]`）
- 分析结论必须有数据支撑，不能凭空判断

## 后续步骤

LLM 完成分析后，将 `sections` 传给 `scripts/build_docx.py` 的 `build_report()` 函数生成 Word 文档：

```python
from scripts.build_docx import build_report
build_report(
    title="...",
    style="research",  # or media / retail
    sections=sections,
    disclaimer="本文基于公开政策文件分析，仅供研究参考，不构成投资建议。",
    output_path="output/report.docx",
)
```

将 `g3_config` 传给 `scripts/build_charts.py` 的 `build_g3_config_matrix()` 生成行业配置图。
