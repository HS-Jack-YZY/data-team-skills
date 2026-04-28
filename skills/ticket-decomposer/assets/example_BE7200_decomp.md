# 需求 DT-2026-04-28-01 对内执行 Plan

- **ticket 标题**：桌面新系列-Basalt系列BE7200 用户偏好与产品定义
- **alignment 版本**：v2（基于：alignment_docs/DT-2026-04-28-01/alignment_v2.md）
- **类型分类**：用户研究 + 产品定义
- **生成时间**：2026-04-29 09:00
- **基于 capabilities.md 版本**：v0.1
- **状态**：v1（首次拆分）

> **假设的需求方反馈**（已合并进 alignment_v2）：Q1=A（仅 3 决策点）·Q2=B（US+DE+UK）·Q3=A（HTML 报告）·Q4=B（Flint2 作上代用户参考组）·Q5=A（**选精准版**，约 30–36h）。alignment_v2 第三章选定档：**精准版 30–36h**。本 Plan 反推工具级后总 h 应在此区间 ±10% 容差内。

---

## 1. 锁定的需求范围

引用自 alignment_v2 第 1 / 4 / 6 章：调研 BE7200（Basalt 首款）的 3 个产品定义决策点（ID / 网口 / USB），覆盖 US + DE + UK 三市场，数据源用 Amazon 评论 + Reddit + GL.iNet 论坛 + OpenWrt 论坛，区分"桌面 vs 旅行"使用场景，输出 HTML 报告（应用 html-report 模板）。Flint2（MT6000）作上代用户参考组列入但不做独立痛点分析。

---

## 2. 拆分思路

应用 **配方 7（产品定义）** 为主框架，叠加 **配方 1（用户研究）** 的数据源模板。"四步流程"组织为：

1. **收数据** —— Amazon 评论（U1）+ Reddit（U2）+ GL.iNet 论坛（U3）+ OpenWrt 论坛（U4）四路并行
2. **打标签** —— 复用 ID / 网口 / USB 三套既有词典 + 场景词扩词（U5）→ 词典标注（U6）→ LLM 语义分析（U7）
3. **做统计** —— 按 3 个决策点切（U8）+ Flint2 上代用户参考组（U9，简短）
4. **给建议** —— HTML 报告 4 章（U10）

依赖关系：U2/U3/U4 与 U1 并行收集 → U5 在抽样语料上扩词（与收集后期并行）→ U6 → U7 → U8 → U10。U9 与 U8 并行（依赖 U7）。

---

## 3. 工作单元清单

### U1. Amazon 评论抓取（自家 4 ASIN + 竞品 4 ASIN · US 主 + DE/UK 自家）

- **输入**：ASIN 清单（自家 BE9300 / BE6500 / Flint4 / MT6000；竞品 ASUS RT-BE92U / TP-Link Archer BE800 / NETGEAR Nighthawk RS500 / Synology BC500）
- **输出产物**：`data/raw/amazon/DT-2026-04-28-01/amazon_reviews_<asin>_<market>_<YYYYMMDD>.csv`
- **预计耗时**：5h（US 8 ASIN × 0.5h = 4h；DE/UK 自家 3 ASIN × 0.5h × 0.66 系数 = 1h）
- **推荐工具**：Apify Amazon 评论（SHADER 代理）
- **基于 P-pattern**：P2
- **依赖**：无
- **可并行兄弟**：U2 / U3 / U4
- **DoD**：
  - 全部 8 ASIN × US 抓取完成；自家 3 ASIN × DE/UK 抓取完成
  - 单 ASIN 行数 ≥ 200（MT6000 ≥ 1000）
  - 字段完整：品牌、型号、评分、标题、正文、日期、市场
- **风险**：MT6000 评论量大可能需要拆批；DE/UK 评论需后续语种处理（已含在 U7）

### U2. Reddit 抓取（决策点关键词 ×6 + 场景词 ×4）

- **输入**：关键词清单——决策点：`router id design`, `router antenna external internal`, `router 2.5g port`, `router sfp+`, `usb-c router`, `router type-c`；场景：`home office router`, `travel router hotel`, `desk router setup`, `roaming router`
- **输出产物**：`data/raw/reddit/DT-2026-04-28-01/reddit_<keyword>_<YYYYMMDD>.csv`（8 列标准字段）
- **预计耗时**：5h（10 关键词 × ~0.5h 实际，因每批 5 关键词，2 批跑批 + 清洗）
- **推荐工具**：Apify Reddit Scraper
- **基于 P-pattern**：P1
- **依赖**：无
- **可并行兄弟**：U1 / U3 / U4
- **DoD**：10 关键词全部跑完；每关键词清洗后行数 ≥ 80（冷门关键词 ≥ 30）；归档到 `data/raw/reddit/DT-2026-04-28-01/`
- **风险**：场景词（"hotel"、"travel"）可能漂到旅行路由器子版块，需在 U6 标注层做后过滤

### U3. GL.iNet 论坛抓取（4 搜索词）

- **输入**：搜索词 `port configuration`, `usb type-c`, `antenna external`, `desktop router setup`
- **输出产物**：`data/raw/forum/glinet/DT-2026-04-28-01/forum_glinet_<keyword>_<YYYYMMDD>.csv`
- **预计耗时**：2h（4 关键词 × 0.5h）
- **推荐工具**：forum_scraper.py（Discourse API）
- **基于 P-pattern**：P3
- **依赖**：无
- **可并行兄弟**：U1 / U2 / U4
- **DoD**：4 搜索词跑完；归档到 `data/raw/forum/glinet/DT-2026-04-28-01/`
- **风险**：GL.iNet 论坛活跃用户偏极客，结论代表性偏 OpenWrt 用户群

### U4. OpenWrt 论坛抓取（2 搜索词）

- **输入**：搜索词 `desktop router hardware`, `usb tethering router`
- **输出产物**：`data/raw/forum/openwrt/DT-2026-04-28-01/forum_openwrt_<keyword>_<YYYYMMDD>.csv`
- **预计耗时**：1h
- **推荐工具**：forum_scraper.py
- **基于 P-pattern**：P3
- **依赖**：无
- **可并行兄弟**：U1 / U2 / U3
- **DoD**：2 搜索词跑完；行数 ≥ 50
- **风险**：用户群高度技术化，对 SFP+ / 万兆需求可能高估

### U5. 场景词扩词（home office vs travel）

- **输入**：U2 第一批回来的抽样语料（先跑 1 关键词试跑取 ≥ 50 条）
- **输出产物**：`dict/scenario_v1.json`（结构：home_office_words / travel_words / aliases）
- **预计耗时**：2h（基于 +4h 弹性的简化版——只标场景词不重做整套词典）
- **推荐工具**：Python + Claude 协助生成词候选 + 人工筛选
- **基于 P-pattern**：P9（扩词变体）
- **依赖**：U2 第一批返回（约 1h 后即可启动）
- **可并行兄弟**：U1 / U3 / U4 后期
- **DoD**：词数 ≥ 20；100 条样本召回率 ≥ 60%
- **风险**：人工筛选耗时漂移；建议组员 review

### U6. 词典标注（ID / 网口 / USB + 场景词）

- **输入**：U1 + U2 + U3 + U4 全部数据 + U5 场景词典
- **输出产物**：`data/labeled/DT-2026-04-28-01/labeled_*.csv`（含 tag_id_design / tag_ports / tag_usb / scenario）
- **预计耗时**：1.5h
- **推荐工具**：Python 脚本（复用 clean_reddit_data.py 风格）
- **基于 P-pattern**：P8
- **依赖**：U1 + U2 + U3 + U4 + U5 全部完成
- **可并行兄弟**：无（汇聚节点）
- **DoD**：标注覆盖率 ≥ 60%；Flint2 数据单独 tag 为 `legacy_user`；归档到 `data/labeled/DT-2026-04-28-01/`
- **风险**：MT6000 评论量大，标注耗时可能 +0.5h

### U7. LLM 语义分析（情感 + 主题聚类）

- **输入**：U6 标注后数据（预计总量 ~3000–4000 条）
- **输出产物**：`data/analyzed/DT-2026-04-28-01/llm_*.csv`（含 sentiment / theme / persona）
- **预计耗时**：4h（~3500 条 × 1h/1000 条 = 3.5h + 校准 0.5h）
- **推荐工具**：Claude API
- **基于 P-pattern**：P10
- **依赖**：U6
- **可并行兄弟**：无
- **DoD**：全部数据有 sentiment 标签；100 条人工 vs LLM 一致性 ≥ 80%；DE/UK 评论先翻译再分析
- **风险**：长文本超 token；可能需要分块

### U8. 决策点统计（ID / 网口 / USB 三个决策点偏好表）

- **输入**：U7 输出
- **输出产物**：3 份偏好表（各决策点的选项支持率 / 情感分布 / 桌面 vs 旅行场景对比）
- **预计耗时**：3h（3 决策点 × 1h）
- **推荐工具**：Python + Pandas + matplotlib
- **基于 P-pattern**：内嵌
- **依赖**：U7
- **可并行兄弟**：U9
- **DoD**：3 个决策点各自有"自家用户 vs 全市场"+"桌面 vs 旅行" 4 象限对比；样本量 < 100 的格子单独标注 `(low confidence)`
- **风险**：场景区分准确率取决于 U5 词典质量

### U9. Flint2 上代用户参考组归类

- **输入**：U7 输出中 `legacy_user = true` 的子集
- **输出产物**：`flint2_reference_summary.md`（半页）
- **预计耗时**：0.5h（按 alignment 第 7 章 Q7=B 的"+0.5h"）
- **推荐工具**：Python + 手工归纳
- **基于 P-pattern**：内嵌
- **依赖**：U7
- **可并行兄弟**：U8
- **DoD**：列出 Flint2 用户在 3 个决策点上的偏好，与全市场对比有差异的列出 ≤ 3 条
- **风险**：Flint2 评论可能偏极客 / OpenWrt 用户，代表性有限——结论中明确

### U10. 章节撰写（HTML 报告 4 章）

- **输入**：U8 + U9 输出
- **输出产物**：`reports/DT-2026-04-28-01/index.html`，4 章：执行摘要 / ID 偏好 / 网口偏好 / USB 偏好（含 Flint2 参考组放在执行摘要内）
- **预计耗时**：6h（4 章 × 1.5h；含 html-report 模板套用 0.5h）
- **推荐工具**：html-report skill + ECharts
- **基于 P-pattern**：P13
- **依赖**：U8 + U9
- **可并行兄弟**：4 章可由不同组员并行写
- **DoD**：
  - 章节内容与 U8 / U9 输出一致
  - 图表用 html-report 的 C 颜色对象
  - 浏览器打开渲染正常（动画 / 响应式）
  - 应用 html-report 设计系统（间距 / 字体 / 阴影）
- **风险**：图表数据手工搬运易错——建议直接 import JSON

---

## 4. 依赖图

```
U1 ──┐
U2 ──┼─→ U6 ─→ U7 ──→ U8 ──┐
U3 ──┤                      ├─→ U10
U4 ──┘                  U9 ─┘
                ↑
U5 (依赖 U2 抽样，与 U3/U4/U1 后期并行)
```

环检查：✅ 无环

---

## 5. 工期估算

- **1 人串行**：Σ(U1+U2+U3+U4+U5+U6+U7+U8+U9+U10) = 5+5+2+1+2+1.5+4+3+0.5+6 = **30h**
- **2 人并行（典型）**：关键路径 = max(U1, U2, U3, U4, U5) → U6 → U7 → max(U8, U9) → U10 = 5 + 1.5 + 4 + 3 + 6 = **19.5h**
- **3 人最大并行**：关键路径 ≈ **18h**（U10 4 章可由 3 人写完）

**与 alignment_v2 一致性自检（Rev 2）**：

- alignment_v2 第三章选定档：**精准版 30–36h**
- 本 Plan 总 h = **30h**
- 偏差判定：30h 落在 30–36h 区间下沿，与中位 33h 的偏差 = -9.1%（在 ±10% 容差内 ✅）

**为什么 B 反推后 h 数与 alignment_v2 对得上**：

- B 用的 capabilities.md 工时基线 = ticket-aligner 计算 h 时所用的同一份基线（单源约定）
- 两 skill 都用 h 作时间单位，无换算误差
- alignment_v2 第二章描述的"业务级数据源"（自家近期产品评论 + 4 款竞品评论 + Reddit + GL.iNet 论坛 + OpenWrt 论坛 + 既有 ID/网口/USB 词典 + HTML 报告）→ B 反推到工具级（U1–U10）后，每个 U 工时来自相同的 capabilities 基线 → 总和自然对得上。

如果偏差超过 ±10%，B **不得**自行抹平——停下来报错让用户检查：是 capabilities.md 不准？alignment_v2 选定档偏差大？还是 alignment_v2 第二章描述漏了某项？

---

## 6. 里程碑 + DoD

### M1：数据全部到位（≈ 启动后 5–7h，2 人并行视角）
- 包含：U1 / U2 / U3 / U4 / U5
- 验收：4 个数据源 CSV 落盘；场景词典 v1 ready

### M2：标注 + 语义分析完成（≈ 启动后 10–12h）
- 包含：U6 / U7
- 验收：labeled_*.csv 与 llm_*.csv 落盘；100 条人工 vs LLM 一致性 ≥ 80%

### M3：统计完成（≈ 启动后 13–14h）
- 包含：U8 / U9
- 验收：3 份决策点偏好表 + Flint2 半页摘要

### M4：HTML 报告交付（≈ 启动后 19–20h）
- 包含：U10
- 验收：浏览器渲染正常；4 章完整；与 alignment_v2 第 6 章 MVP 承诺对齐

---

## 7. 风险登记

| 风险类型 | 触发的 U | 缓解措施 |
|---|---|---|
| Apify 限流 | U2 (Reddit) | 每批 ≤ 5 关键词，分 2 批跑 |
| MT6000 评论量大 | U1 / U6 | 提前预留 +0.5h 缓冲；可拆 U1-MT6000 单独 1.5h |
| DE/UK 跨语种 | U7 | 先翻译再 LLM；预留 +1h |
| 场景词典准确率不足 | U5 / U6 / U8 | U5 完成后做 100 条人工抽检；不达标返工 +1h |
| Flint2 用户代表性偏窄 | U9 | 结论中明确"上代用户偏极客 / OpenWrt"，不强行外推 |
| 图表数据手工搬运 | U10 | 强制直接 import JSON，不复制粘贴数字 |

---

## 此示例的设计意图（仅供组员参考）

这是 BE7200 ticket 的下游 Plan，对照：
- 上游 alignment_v2.md（基于 `assets/example_BE7200.md` + 假设需求方反馈）
- 同事既有的 research_flow.md（实际执行的工作流）

观察重点：

- **总 h 与 alignment 第 6 章 MVP 一致**（30h vs 33h，-9% 在容差内）。差异来源在第 5 章工期估算下方解释。
- **每个 U ≤ 8h**，最大的 U10（6h）+ U1/U2（5h）。如果某 U 因实际情况超 8h，按维度再拆。
- **U 之间依赖图无环**，由 U1–U4 并行 → U6 汇聚 → U7 → U8/U9 并行 → U10 收尾。
- **不分配人名**，让组员在 IM 下抢单：例如"我接 U1 + U6"、"我接 U2 + U7"。
- **风险登记直接关联 U**，让抢单时就能看到"接 U2 要小心 Reddit 限流"。

skill 在生成此类 Plan 时**不要**让 U 数膨胀（避免 30+ 个 U），也**不要**让 U 颗粒度过粗（避免单 U > 8h）。10 个左右的 U 是中等 ticket 的甜点区。
