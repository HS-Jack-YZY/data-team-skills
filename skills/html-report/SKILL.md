---
name: html-report
description: >
  GL.iNet 数据组的 HTML 报告标准模板与设计系统。用于生成老板报告、季度/月度复盘、广告复盘、
  数据分析报告、专项分析、内部 HTML 报告等正式产出。基于 reports/boss_report_2026Q1/index.html
  沉淀而成，统一使用"黄昏绮景"7 色调色板（来源：`References/IMG_8521.JPG` · 科研Sci配色）、
  Plus Jakarta Sans + Noto Sans SC 字体栈、ECharts v5 图表、响应式布局。

  当用户提到以下任意场景时，必须使用这个 skill，不要自创样式：
  老板报告 / boss report / 数据组报告 / 季度复盘 / 月度复盘 / Q1 / Q2 / Q3 / Q4 报告 /
  广告复盘 / 销售复盘 / HTML 报告 / 内部报告 / 数据分析报告 / 组内标准报告 /
  按老板报告模板写 / 用组内模板 / 做一份 XX 报告 / 写一份 HTML 报告 /
  generate report / write a report / create a dashboard report.

  即使用户没有明确说"用模板"，只要是要生成正式的内部数据分析 HTML 产出，就加载此 skill。
  不要手搓样式、不要用其他图表库、不要改调色板。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# html-report — 组内 HTML 报告标准模板

这份 skill 把 `reports/boss_report_2026Q1/index.html` 沉淀成组内写报告的统一标准。目标是让每份新报告都视觉一致、语义清晰、符合既定设计系统。

---

## 核心契约（不要违反）

1. **不修改 `:root` 变量名和色值** —— 7 主色 + 中性色 + 阴影 + 圆角是组内契约，改了就破坏视觉一致性
2. **只用 ECharts v5（CDN）** —— 不引入 Chart.js、D3、ApexCharts、Plotly 等其他图表库
3. **CSS 保持内联** —— 报告是单文件可分发的产物，不外置 CSS
4. **图表颜色从全局 `C` 对象取** —— 不硬编码 HEX 值到图表 option 里
5. **语义色映射** —— 绿色（`--teal-mid`）=达标/增长/盈利；金色（`--gold`）=接近阈值；橙色（`--orange`）=警告/行动项；珊瑚红（`--coral`）=未达标/下降/亏损
6. **中英文字体分轨** —— 英文数字走 Plus Jakarta Sans，中文走 Noto Sans SC / PingFang SC

---

## 工作流（用户触发后按序执行）

### Step 1：读模板作为起点
```
Read assets/template.html
```
**不要从零写 HTML。** 模板已经包含了全部 CSS 设计令牌、组件样式、响应式规则、ECharts 工厂函数（`C` 颜色对象、`tooltipStyle()`、`axisStyle()`、`lerpColor()`）。

### Step 2：和用户确认报告范围
问这些问题（若用户已提供则跳过）：
- 报告期？（YYYY-MM / YYYY-Q1 / 跨期）
- 数据来源？（AMC / SP-API / 第三方 / 人工汇总）
- 主要章节需要几段？典型结构：概览 → 漏斗/细分 → 总结建议
- 要不要图表？什么类型？

### Step 3：确定章节骨架
参考 `references/content-structure.md` 里的章节模式：
- **月度/季度复盘**：概览达标 → 广告/投放/流量详情 → 5 个子主题细分 → 总结行动（推荐结构）
- **专项分析**：背景 → 关键发现 → 数据论证 → 结论
- **漏斗诊断**：全链路漏斗 → 层级瓶颈分析 → 对照策略 → 行动
- **对比分析**：对照组定义 → 关键指标对比 → 显著性判断 → 解读

### Step 4：按需读组件库与图表范式
只在需要时读，不要提前全读：
- 做 KPI 卡 / 漏斗 / Insight 框 / Summary 编号列表 → `Read references/components.md`
- 做柱图 / 折线 / 饼图 / 双 Y 轴混合 / 堆积 → `Read references/charts.md`

### Step 5：生成目标文件
产出路径约定：`reports/<报告名>/index.html`（与现有 `reports/` 目录结构保持一致）。
复制 template.html → 改 title → 改 header → 按章节填充 → 替换所有 `{{占位符}}`。

### Step 6：验证
- 浏览器打开看一下渲染效果（让用户自己打开，或用 `open reports/<name>/index.html`）
- 检查：动画是否正常、hover 是否有反馈、响应式在窄屏是否换行、图表是否出现
- 如果是 macOS：`open /Users/yuanzheyi/GL-iNet/Projects/DataTeam/reports/<name>/index.html`

---

## 设计系统速览

### 配色 · 黄昏绮景（来源：`References/IMG_8521.JPG` · 科研Sci配色）

| HEX | CSS 变量 | 语义角色 |
|---|---|---|
| `#274753` | `--teal-deep` / `--slate` | 最深：主文字、最高强调、冷色调龙头 |
| `#297270` | `--teal` / `--blue` | 主品牌色、section-label、徽章文字 |
| `#299d8f` | `--teal-mid` / `--emerald` | **达标 / 增长 / 盈利** |
| `#8ab07c` | `--sage` | 过渡绿、辅助色条 |
| `#e7c66b` | `--gold` | **接近阈值 / 中性警告 / 未达标边框** |
| `#f3a361` | `--orange` / `--amber` | **警告 / 行动项 / 环形进度（missed）** |
| `#e66d50` | `--coral` / `--red` | **未达标 / 下降 / 亏损** |

**氛围**：冷色（teal 系）做基底占 70% 面积，绿色（sage）做过渡占 10%，暖色（gold/orange/coral）做强调占 20%。不要用冷色表示警告、也不要用暖色表示增长。

### 字体

```css
font-family: 'Plus Jakarta Sans', 'Noto Sans SC', 'PingFang SC',
             'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

字号体系：10/11/12/13/14/15/17/22/28/32 px（离散使用，不要插入中间值）。标题用 800 权重，数值用 800 权重，正文用 400。

### 间距

8 的倍数：`8 / 12 / 14 / 16 / 20 / 24 / 28 / 36 / 40 px`。`.section` 内边距固定 `36px 40px`；`.container` 最大宽度 1160px。

### 圆角 & 阴影

- 卡片大圆角：`var(--radius)` = 14px
- 小组件：`var(--radius-sm)` = 8px
- 漏斗条：4px
- 阴影三级：`--shadow-sm` / `--shadow` / `--shadow-lg`（hover 时提升）

---

## 组件速查（详细见 references/components.md）

| 组件 | 类名 | 用途 | 何时用 |
|---|---|---|---|
| 封面 | `.report-header` + `.header-accent` | 报告标题 + meta 表 | 每份报告唯一 |
| 章节容器 | `.section` + `.section-label` | 主章节（border-top 颜色自动分化） | 每个主章节 |
| 环形 KPI | `.ach-kpi-card.reached/.missed` | 带达标率的关键指标 | 概览章节 |
| 扁平 KPI | `.ad-kpi-card` / `.ad-kpi-card.highlight` | 纯数值指标 | 明细章节 |
| 漏斗 | `.funnel-grid` + `.fg-row`（`display:contents`） | 多层级转化分析 | 漏斗章节 |
| 洞察框 | `.insight` / `.insight.warning` | 重点结论高亮 | 每张图表后 |
| 总结列表 | `.summary-grid` + `.summary-col.actions` | 结论 + 行动 2 列 | 最后一章 |
| 数据表 | `.asin-tbl` / `.dsp-tbl` | 详细明细 | 需要展示多行数据时 |
| 图表容器 | `.chart-box` | ECharts 挂载点 | 需要图表时 |
| 分隔线 | `.divider` | 章节内分段 | 一个 section 内多个话题 |

---

## 常见指令映射（用户说 → 你做什么）

| 用户说 | 你应该做 |
|---|---|
| "加一个 KPI 卡" | 用 `.ad-kpi-card`，若需"达标/未达标"语义用 `.ach-kpi-card.reached/.missed` |
| "做一个漏斗" | 用 `.funnel-grid` + `.fg-row`（`display:contents`）；颜色依层次 `blue → green → orange → grey-bar` |
| "加一段结论" | 用 `.insight`（正面）或 `.insight.warning`（警示） |
| "加一个柱图" | ECharts + `C` 颜色对象 + `tooltipStyle()` + `axisStyle()`，见 `references/charts.md` |
| "加趋势图" | ECharts 双 Y 轴混合（柱+折线），带 `endLabel` |
| "加对比数据" | `.asin-tbl` 右对齐 + `.col-win`（绿）/ `.col-loss`（红）着色 |
| "加目录/锚点" | 用 `<a href="#section-id">` 锚点导航；不要引入 JS 路由 |
| "做成 PDF" | 浏览器 Cmd+P；必要时补 `@media print { box-shadow: none; }` |
| "改配色" | **拒绝**。解释这是组内契约；如果真的需要新风格，建议新建不同 skill |

---

## 反模式（这些情况不要做）

- ❌ 从零手写 `<style>` —— 直接用 template.html 的内联 CSS
- ❌ 引入 Tailwind / Bootstrap / Material UI
- ❌ 引入 Chart.js / D3 / Plotly / ApexCharts
- ❌ 写 `style="color:#ffaa00"` 这种硬编码色值 —— 用 CSS 变量
- ❌ 用浅色表示亏损（如浅绿色的负数）—— 必须 `--coral`
- ❌ 把 CSS 单独拆成文件 —— 保持内联
- ❌ 用 React / Vue 组件 —— 这是静态 HTML 产物
- ❌ 用 `<div class="container">` 以外的容器做外层布局

---

## 文件结构

```
.claude/skills/html-report/
├── SKILL.md                     # 你正在读的这个文件
├── assets/
│   ├── template.html            # 骨架模板（Step 1 读这个）
│   ├── tokens.css               # 独立的 :root 变量副本（Python 脚本配色参考）
└── references/
    ├── components.md            # 组件库详细代码段（按需读）
    ├── charts.md                # ECharts 5 种常用图表配置（按需读）
    └── content-structure.md     # 不同报告类型的章节骨架（按需读）
```

---

## 参考源

- **母版**：`reports/boss_report_2026Q1/index.html`（组内既成事实）
- **配色出处**：`References/IMG_8521.JPG`（"科研Sci配色 · 黄昏绯景"）
- **产出惯例**：参考 `reports/` 目录下其他已完成报告的文件夹结构（index.html + assets/ + data/）
