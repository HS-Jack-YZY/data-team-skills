# 组件库 · components.md

这份文档是 `assets/template.html` 里所有组件的**配方卡**：每个组件给出 HTML 结构、关键 CSS 类、使用变体和适用场景。当需要往报告里加具体某种组件时来这里查。

**使用规则**：
- 组件 CSS 已全部在 `template.html` 的 `<style>` 里定义，直接复制 HTML 片段即可生效
- 不要改类名，不要自创新的 class
- 颜色通过变体类（如 `.reached` / `.missed` / `.warning`）切换，不要 inline style 改颜色

---

## 目录

- [1. Header 封面](#1-header-封面)
- [2. Section 章节容器](#2-section-章节容器)
- [3. 环形 KPI 卡（达标/未达标）](#3-环形-kpi-卡达标未达标)
- [4. 扁平 KPI 卡（数值展示）](#4-扁平-kpi-卡数值展示)
- [5. 漏斗网格](#5-漏斗网格)
- [6. Insight 洞察框](#6-insight-洞察框)
- [7. Summary 结论/行动列表](#7-summary-结论行动列表)
- [8. 数据表格](#8-数据表格)
- [9. 图表容器](#9-图表容器)
- [10. 分隔线 / 术语表 / Tooltip](#10-分隔线--术语表--tooltip)

---

## 1. Header 封面

**语义**：整份报告的封面。左侧 6px 渐变色条 + 右侧徽章 + H1 标题 + 4 格 meta 表。

```html
<header class="report-header">
  <div class="header-accent"></div>
  <div class="header-body">
    <div class="header-eyebrow">
      <span class="header-badge">GL.iNet · 内部报告</span>
    </div>
    <h1>2026年3月 广告复盘报告</h1>
    <div class="header-meta">
      <div class="meta-cell">
        <div class="meta-label">报告期</div>
        <div class="meta-value">2026-03</div>
      </div>
      <div class="meta-cell">
        <div class="meta-label">数据来源</div>
        <div class="meta-value">AMC</div>
      </div>
      <div class="meta-cell">
        <div class="meta-label">归因窗口</div>
        <div class="meta-value">30 天</div>
      </div>
      <div class="meta-cell">
        <div class="meta-label">撰写</div>
        <div class="meta-value">Data Team</div>
      </div>
    </div>
  </div>
</header>
```

**要点**：
- 徽章（`.header-badge`）格式固定：`组织 · 报告类型`，例如 `"GL.iNet · 内部报告"`、`"GL.iNet · 月度复盘"`
- H1 控制在 18-30 字以内，超长会换行不好看
- meta-cell 数量建议 3-5 个；`.header-meta` 在 900px 以下自动变 2 列

---

## 2. Section 章节容器

**语义**：每个主章节的外层容器。border-top 颜色按 `:nth-child(2/3/4/5)` 自动从深到浅（`--teal-deep → --teal → --teal-mid → --sage`），**不需要手动指定颜色**。

```html
<div class="section">
  <div class="section-label">第一部分</div>
  <h2>章节标题</h2>
  <div class="desc">1-2 句话描述章节主题、数据来源、口径说明。</div>

  <!-- 章节内容 -->
</div>
```

**子元素**：
- `.section-label`：章节编号（"第一部分"、"第二部分"）。前置小横条由 `::before` 自动生成。
- `h2`：章节大标题，22px / 800 权重
- `.desc`：描述文本，14px / 400 权重 / 最大宽 820px
- `.ach-section-title`：子章节小标题，15px / 700 权重
- `.ach-section-hint`：子标题下的小字说明，12px

**超过 5 个章节怎么办？** 第 6 个及以后的 border-top 会是透明，不影响使用；如果想要延续色阶，手动加一行 CSS：
```html
<style> .section:nth-child(6) { border-top-color: var(--gold); } </style>
```

---

## 3. 环形 KPI 卡（达标/未达标）

**语义**：带环形进度条的关键指标，用于"目标达成"场景。两种状态：
- `.reached`：达标（绿色环 + 绿边框）
- `.missed`：未达标（橙色环 + 金色边框）

**关键机制**：`style="--ring-pct:NN"` 动态控制环形百分比（0-100）。

### 达标卡（reached）

```html
<div class="ach-kpi-card reached" style="--ring-pct:100">
  <div class="kpi-ring"><span class="kpi-ring-label">100%</span></div>
  <div class="ach-status">Router</div>
  <div class="ach-actual">¥4,348<span class="ach-actual-unit">万</span></div>
  <div class="ach-actual-label">3月实际销售额</div>
  <div class="ach-rate">达标率 100.1%</div>
  <div class="ach-detail">目标 ¥4,343万</div>
  <div class="ach-delta">差额 +¥5万</div>
</div>
```

### 未达标卡（missed）

```html
<div class="ach-kpi-card missed" style="--ring-pct:77.3">
  <div class="kpi-ring"><span class="kpi-ring-label">77%</span></div>
  <div class="ach-status">KVM</div>
  <div class="ach-actual">¥661<span class="ach-actual-unit">万</span></div>
  <div class="ach-actual-label">3月实际销售额</div>
  <div class="ach-rate">达标率 77.3%</div>
  <div class="ach-detail">目标 ¥855万</div>
  <div class="ach-delta">差额 &minus;¥194万</div>
</div>
```

### 网格容器

```html
<div class="ach-kpi-grid">
  <!-- 1-3 张卡片 -->
</div>
```

**要点**：
- 默认 3 列（`grid-template-columns: repeat(3, 1fr)`），900px 以下变单列
- 如果只有 2 张卡，可以用 `style="grid-template-columns: 1fr 1fr"` 覆盖
- 超过 5 张卡不推荐用这个组件，改用扁平 `.ad-kpi-card`

---

## 4. 扁平 KPI 卡（数值展示）

**语义**：没有"达标/未达标"语义的纯数值卡，适合广告花费、DAU、ROAS 等纯度量指标。

```html
<div class="ad-kpi-grid">
  <div class="ad-kpi-card highlight">
    <div class="ad-kpi-label">总广告花费</div>
    <div class="ad-kpi-value">¥370<span class="unit">万</span></div>
    <div class="ad-kpi-sub">PPC + DSP 合计</div>
  </div>
  <div class="ad-kpi-card">
    <div class="ad-kpi-label">TACOS</div>
    <div class="ad-kpi-value">7.4<span class="unit">%</span></div>
    <div class="ad-kpi-sub">广告总花费 / 总销售额</div>
  </div>
  <!-- 最多 4 张 -->
</div>
```

**变体**：
- `.ad-kpi-card`：默认白底
- `.ad-kpi-card.highlight`：绿色渐变背景 + 绿色强调，用于"最重要的那个"
- `.ad-kpi-card.warn`（仅在 basket-highlight-row 里）：金色背景，用于"偏离基线"

**要点**：
- 网格默认 4 列，900px 以下变 2 列
- `highlight` 最多 1-2 张，否则失去强调意义

---

## 5. 漏斗网格

**语义**：多层级转化分析。用 CSS Grid + `display: contents` 实现"行式"布局而无额外 DOM 嵌套。

```html
<div class="funnel-grid">
  <!-- 表头 -->
  <div class="fg-head"></div>
  <div class="fg-head">User Count</div>
  <div class="fg-head" style="color:var(--blue)">Primary KPI</div>
  <div class="fg-head">Efficiency</div>
  <div class="fg-head" style="color:var(--orange)">Guardrail</div>

  <!-- 第 1 层 -->
  <div class="fg-row">
    <div class="fg-label">
      <div class="name">Awareness</div>
      <div class="sub">触达</div>
    </div>
    <div class="fg-bar">
      <div class="funnel-bar blue" style="width:100%">9.5M</div>
    </div>
    <div class="fg-metric">
      <span class="ml">Unique Reach</span>
      <span class="mv">9,504,580</span>
    </div>
    <div class="fg-metric">
      <span class="ml">CPM</span>
      <span class="mv">$4.86</span>
    </div>
    <div class="fg-metric">
      <span class="ml">Viewability</span>
      <span class="mv">82%</span>
    </div>
  </div>

  <!-- 转化率徽章（跨全宽，放在两层之间） -->
  <div class="fg-rate">
    <span class="rate-badge">↓ 5.9%</span>
    <span class="rate-label">触达 → 种草</span>
  </div>

  <!-- 第 2 层：funnel-bar 改色 -->
  <div class="fg-row">
    <div class="fg-label"><div class="name">Interest</div><div class="sub">种草</div></div>
    <div class="fg-bar"><div class="funnel-bar green" style="width:60%">560K</div></div>
    <!-- metrics ... -->
  </div>
</div>
```

**漏斗条颜色语义**（按层级从上到下递进）：
- `.funnel-bar.blue` —— 第 1 层（最上面，触达）
- `.funnel-bar.green` —— 第 2 层（种草/兴趣）
- `.funnel-bar.orange` —— 第 3 层（购买前）
- `.funnel-bar.grey-bar` —— 第 4 层（最终转化/留存）

**width 控制条长**：`style="width:NN%"`，按各层相对第一层的比例计算。

**`.fg-metric` 数值着色**：
- `.mv.pos`：正向（绿）
- `.mv.neg`：负向（红）
- `.mt.target`：基线参考（teal）
- `.mt.guardrail`：护栏阈值（橙）

**关键字标签（可选）**：每层底下展示关键词/路径
```html
<div class="fg-terms-spacer"></div>
<div class="fg-terms">
  <span class="term-tag">keyword1</span>
  <span class="term-tag">keyword2</span>
</div>
```

---

## 6. Insight 洞察框

**语义**：章节内的结论高亮。两种变体：
- `.insight`：正面/中性（teal 渐变 + teal 左边框）
- `.insight.warning`：警示（金色渐变 + 橙色左边框）

```html
<!-- 正面结论 -->
<div class="insight">
  <strong>DSP 投放效率优秀：</strong>综合 ROAS 达 <strong>8.2x</strong>，Router 新客占比 66.5%。
</div>

<!-- 警示结论 -->
<div class="insight warning">
  <strong>重点关注：</strong>KVM 缺口 <strong>¥194万（-22.7%）</strong>，拖累整体未达标。
</div>
```

**要点**：
- 每张图表、每组 KPI 卡之后建议加 1 个 insight 框，让读者知道"重点是什么"
- `<strong>` 会自动染色（正面→teal，警示→orange）；不要加 inline color
- 控制文字长度 1-3 行，超长用正文段落而不是 insight

---

## 7. Summary 结论/行动列表

**语义**：报告最后一章的 2 列收尾。左列"结论"（蓝色编号），右列"行动"（橙色编号）。**CSS counter 自动编号**。

```html
<div class="summary-grid">
  <div class="summary-col">
    <h4>3 个核心结论</h4>
    <ol>
      <li>整体达标 96.4%，<strong>唯一痛点是美国 KVM</strong>。</li>
      <li>非品牌广告直接归因看似亏损，<strong>种草归因下真实回报 4.0x</strong>。</li>
      <li>5 个市场分化明显：品牌词与 Cellular 在赢，KVM 流量已就位。</li>
    </ol>
  </div>
  <div class="summary-col actions">
    <h4>3 个 Q2 行动建议</h4>
    <ol>
      <li><strong>美国 KVM 专项排查</strong>：立刻立项。</li>
      <li><strong>维持/加码非品牌广告</strong>，特别是竞品定向。</li>
      <li><strong>Home Router 蓝海加投测试</strong>。</li>
    </ol>
  </div>
</div>
```

**要点**：
- 左列 `.summary-col` / 右列 `.summary-col.actions`（`.actions` 让编号变橙）
- `<ol>` 用原生，编号不用自己写
- 一般每列 3-5 条，多了读者抓不住
- `<strong>` 高亮关键短语（自动 teal 色）

---

## 8. 数据表格

**语义**：详细明细数据展示。两个样式类：`.asin-tbl` 和 `.dsp-tbl`（仅细节差异，功能等价）。

```html
<table class="asin-tbl">
  <thead>
    <tr>
      <th class="col-left">产品</th>
      <th>花费</th>
      <th>销售</th>
      <th>ROAS</th>
      <th>ACoS</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="col-left">Product A</td>
      <td>$1,234</td>
      <td class="col-win">$12,340</td>
      <td class="col-accent">10.0x</td>
      <td>10%</td>
    </tr>
    <tr>
      <td class="col-left">Product B</td>
      <td>$2,500</td>
      <td class="col-loss">$1,800</td>
      <td class="col-loss-bold">0.72x</td>
      <td>139%</td>
    </tr>
  </tbody>
</table>
```

**列着色**：
- `.col-left`：该列左对齐（默认右对齐）
- `.col-win`：绿色粗体（盈利/达标）
- `.col-loss`：珊瑚红（亏损/未达标）
- `.col-loss-bold`：珊瑚红粗体（严重负向）
- `.col-accent`：最深 teal 粗体（最高强调）

**dsp-tbl 特有**：
- `.subtotal` 行：浅灰背景（分组小计）
- `.total` 行：teal 背景（总计）
- `.col-teal` / `.col-gold`：按品类的品牌色

---

## 9. 图表容器

**语义**：ECharts 挂载点。只管容器，内容见 `references/charts.md`。

```html
<div class="chart-box" id="chart-my-viz" style="height:320px; margin-top:12px"></div>
```

**要点**：
- `id` 必须唯一（同一页面多个图表时）
- 高度可通过 inline `style="height:NNpx"` 覆盖；默认 380px
- 图表初始化代码放到 `<script>` 末尾的 IIFE 里（见 charts.md）

---

## 10. 分隔线 / 术语表 / Tooltip

### 分隔线

章节内多话题切换时用：

```html
<div class="divider"></div>
```

渐变线条，两端淡出。

### 术语表（可选）

报告末尾放术语定义：

```html
<div class="glossary">
  <h4>术语表</h4>
  <dl>
    <dt>TACOS</dt>
    <dd>Total ACoS = 广告花费 ÷ 总销售额（含自然单）</dd>
    <dt>NTB</dt>
    <dd>New-to-Brand 新客</dd>
  </dl>
</div>
```

### Tooltip（悬停提示）

```html
<span class="tooltip-trigger">
  指标名 <sup>?</sup>
  <span class="tooltip-box">这个指标的含义解释</span>
</span>
```

hover 时提示框从上方出现，自动居中对齐。适合在表头或 KPI 标签里使用。
