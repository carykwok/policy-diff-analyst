# Profile: 政府工作报告 (govt_work_report)

## Layer set

- A1 宏观定调
- A2 政策工具
- A3 产业地图
- A4 风险监管
- A5 民生分配
- A6 区域对外
- A7 结构增量

## Layer keyword maps (A1–A7)

### A1 宏观定调
- 量化指标关键词：GDP / 国内生产总值、赤字率、CPI / 居民消费价格、城镇新增就业
- 基调锚定短语：稳中求进、稳中有进、高质量发展、以进促稳

### A2 政策工具
- 货币：稳健、灵活适度、精准有力、降准、降息、结构性货币政策工具
- 财政：赤字率、专项债、超长期特别国债、减税降费

### A3 产业地图
- 科技：新质生产力、人工智能、AI、算力、半导体、集成电路、量子、生物制造
- 制造：新能源、智能制造、高端装备、工业母机
- 安全：能源安全、粮食安全、产业链供应链、国产替代
- 消费：汽车、地产、服务消费、文旅

### A4 风险监管
- 房地产、地方债务、金融风险、平台经济、防范化解

### A5 民生分配
- 居民收入、社保、医保、养老、生育、教育、医疗

### A6 区域对外
- 区域：京津冀、长三角、粤港澳、成渝、东北、西部
- 对外：对外开放、一带一路、外资、进博会

### A7 结构增量
横切层，由 diff 引擎基于 A1-A6 的 added/removed/intensity_shift 自动聚合。

## Quantitative keys

量化指标（Sheet 1「指标对比」用）：
- GDP、国内生产总值
- 赤字率
- CPI、居民消费价格
- 城镇新增就业

## Strength scoring anchors (0–5 scale)

Applied to verbs/modifiers in each layer to compute B2 scores:

| 措辞 | 得分 |
|------|------|
| 坚决、坚定、全面 | 5 |
| 大力、着力、切实 | 4 |
| 加快、积极、深入 | 3 |
| 稳妥、有序、逐步 | 2 |
| 审慎、适度、研究 | 1 |
| (未提及) | 0 |

Scoring rule: for each A1–A6 layer, aggregate the highest-scoring modifier within ±10 Chinese characters of any layer keyword. Mean across all hits = layer score.

## Notes
- This profile is v1 for 政府工作报告 only. Later profiles override/extend.
- Keep keyword list focused — max 10 per layer sub-bucket to avoid noise.
