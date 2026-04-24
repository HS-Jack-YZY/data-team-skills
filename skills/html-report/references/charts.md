# ECharts 图表配方 · charts.md

这份文档是组内报告 5 种常用图表的**配置模板**。所有模板都：
- 依赖 template.html 已定义的全局 `C` 颜色对象 + `tooltipStyle()` + `axisStyle()` + `lerpColor()`
- 遵守组内 `backgroundColor: 'transparent'` 约定
- 监听 `window.resize` 自动响应

**使用规则**：
- 不要硬编码 HEX 颜色，用 `C.tealMid` / `C.coral` 等
- 不要换图表库
- 不要关闭 tooltip / hover 交互
- `barWidth: '52%'`、`radius: ['48%', '72%']` 等尺寸参数来自现有模板，建议保留

---

## 目录

- [1. 横向柱图（Ranking / 达标率）](#1-横向柱图ranking--达标率)
- [2. 分组柱图（对比 A vs B）](#2-分组柱图对比-a-vs-b)
- [3. 双 Y 轴混合（柱 + 折线，趋势分析）](#3-双-y-轴混合柱--折线趋势分析)
- [4. 环形饼图（构成占比）](#4-环形饼图构成占比)
- [5. 堆积柱图（多维度叠加）](#5-堆积柱图多维度叠加)

每个模板包含：HTML 容器 + `<script>` IIFE 初始化代码。复制粘贴即可，只需替换数据数组。

---

## 共用的全局工具（template.html 已内置）

**色值对象**：
```javascript
var C = {
  tealDeep:'#274753', teal:'#297270', tealMid:'#299d8f',
  sage:'#8ab07c', gold:'#e7c66b', orange:'#f3a361', coral:'#e66d50',
  blue:'#297270', slate:'#274753', muted:'#5e8a87',
  border:'#d8e5e2', grid:'#f0f5f3',
  tooltipBg: 'rgba(39,71,83,0.92)',
};
```

**tooltip 样式**：`tooltipStyle()` 返回深灰半透明背景 + 白字 + 8px 圆角。总是用 `Object.assign(tooltipStyle(), { trigger: ..., formatter: ... })` 展开。

**坐标轴样式**：`axisStyle(nameColor)` 返回浅 border 线 + muted 灰色 label + 虚线 splitLine。

**颜色插值**：`lerpColor(lightHex, darkHex, t)`，`t ∈ [0,1]`，用于"按数值深浅着色"效果。常用对组：
- Teal 族（Router / 达标）：`'#b0d8d4' → '#1e4e4c'`
- Gold 族（KVM / 警告）：`'#eddea0' → '#a67520'`

---

## 1. 横向柱图（Ranking / 达标率）

**适用**：多个区域/品类按某个指标排序对比，尤其是达标率（有 100% 基线参照）。

```html
<div class="chart-box" id="chart-regional-rate" style="height:330px;"></div>
```

```javascript
(function () {
  var dom = document.getElementById('chart-regional-rate');
  if (!dom) return;
  var chart = echarts.init(dom);

  var regions = ['JP', 'EU', 'CA', 'US&MX', 'UK', 'AU'];
  var rates   = [119.4, 102.9, 96.8, 94.5, 93.2, 88.9];  // 达标率 %

  // 按数值深浅着色
  function rateT(r) { return (r - 85) / 40; }  // 85-125 映射到 0-1
  var barColors = rates.map(function (r) {
    return lerpColor('#b0d8d4', '#1e4e4c', rateT(r));
  });

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: Object.assign(tooltipStyle(), {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (params) {
        var p = params[0];
        var col = p.value >= 100 ? C.tealMid : C.coral;
        return '<b>' + p.name + '</b><br/>达标率：<b style="color:' + col + '">' + p.value + '%</b>';
      }
    }),
    grid: { left: 72, right: 130, top: 16, bottom: 28 },
    xAxis: {
      type: 'value', max: 135,
      axisLabel: { color: C.muted, formatter: '{value}%' },
      axisLine: { lineStyle: { color: C.border } }, axisTick: { show: false },
      splitLine: { lineStyle: { color: C.grid, type: 'dashed' } }
    },
    yAxis: {
      type: 'category', data: regions,
      axisLabel: { fontSize: 13, fontWeight: 'bold', color: C.slate },
      axisLine: { show: false }, axisTick: { show: false }
    },
    series: [{
      type: 'bar', barWidth: '52%',
      data: rates.map(function (r, i) {
        return { value: r, itemStyle: { color: barColors[i], borderRadius: [0,4,4,0] } };
      }),
      label: {
        show: true, position: 'right', fontSize: 12, fontWeight: 'bold',
        formatter: function (p) { return p.value + '%' + (p.value >= 100 ? '  ✓' : ''); },
        color: function (p) { return barColors[p.dataIndex]; }
      },
      markLine: {
        silent: true, symbol: 'none', data: [{ xAxis: 100 }],
        lineStyle: { color: C.coral, type: 'dashed', width: 2 },
        label: { formatter: '目标 100%', color: C.coral, fontSize: 11, position: 'insideEndTop' }
      }
    }]
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

**关键细节**：
- `markLine xAxis: 100` 画 100% 基线
- 数值右侧用 `✓` 标记达标项
- `borderRadius: [0,4,4,0]` 只让右端圆角（符合从左向右的视觉流）

---

## 2. 分组柱图（对比 A vs B）

**适用**：同一批类目下对比两个系列，比如 Router vs KVM、同比 vs 环比。

```html
<div class="chart-box" id="chart-grouped" style="height:360px;"></div>
```

```javascript
(function () {
  var dom = document.getElementById('chart-grouped');
  if (!dom) return;
  var chart = echarts.init(dom);

  var regions = ['US&MX', 'CA', 'UK', 'EU', 'AU', 'JP'];
  var routerRates = [100.7, 97.7, 93.2, 103.3, 87.4, 118.9];
  var kvmRates    = [69.6, 90.1, 93.9, 99.2, 107.1, 121.4];

  function rateT(r) { return (r - 65) / 60; }
  var routerColors = routerRates.map(function (r) { return lerpColor('#b0d8d4', '#1e4e4c', rateT(r)); });
  var kvmColors    = kvmRates.map(function (r) { return lerpColor('#eddea0', '#a67520', rateT(r)); });

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: Object.assign(tooltipStyle(), {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (params) {
        var html = '<b>' + params[0].name + '</b><br/>';
        params.forEach(function (p) {
          var col = p.value >= 100 ? C.tealMid : C.coral;
          html += p.marker + p.seriesName + '：<b style="color:' + col + '">' + p.value + '%</b><br/>';
        });
        return html;
      }
    }),
    legend: { data: ['Router', 'KVM'], top: 4, textStyle: { color: C.muted } },
    grid: { left: 48, right: 16, top: 44, bottom: 36 },
    xAxis: {
      type: 'category', data: regions,
      axisLabel: { fontSize: 12, fontWeight: 'bold', color: C.slate },
      axisLine: { lineStyle: { color: C.border } }, axisTick: { show: false }
    },
    yAxis: {
      type: 'value', min: 60,
      axisLabel: { color: C.muted, formatter: '{value}%' },
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: C.grid, type: 'dashed' } }
    },
    series: [
      {
        name: 'Router', type: 'bar', barWidth: '28%',
        data: routerRates.map(function (r, i) {
          return { value: r, itemStyle: { color: routerColors[i], borderRadius: [4,4,0,0] } };
        }),
        label: { show: true, position: 'top', fontSize: 10, fontWeight: 'bold',
          formatter: function (p) { return p.value + '%'; },
          color: function (p) { return routerColors[p.dataIndex]; } },
        markLine: {
          silent: true, symbol: 'none', data: [{ yAxis: 100 }],
          lineStyle: { color: C.coral, type: 'dashed', width: 2 },
          label: { formatter: '100%', color: C.coral, fontSize: 10, position: 'insideEndTop' }
        }
      },
      {
        name: 'KVM', type: 'bar', barWidth: '28%',
        data: kvmRates.map(function (r, i) {
          return { value: r, itemStyle: { color: kvmColors[i], borderRadius: [4,4,0,0] } };
        }),
        label: { show: true, position: 'top', fontSize: 10, fontWeight: 'bold',
          formatter: function (p) { return p.value + '%'; },
          color: function (p) { return kvmColors[p.dataIndex]; } }
      }
    ]
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

**关键细节**：
- 两个 series 共用 `barWidth: '28%'` 让柱子均匀分布
- 第一个 series 挂 `markLine`（100% 基线）就够了，第二个不用重复
- `borderRadius: [4,4,0,0]` 只让顶部圆角

---

## 3. 双 Y 轴混合（柱 + 折线，趋势分析）

**适用**：时间序列中需要同时展示两类不同量纲的指标。例如搜索量（大数量级）+ 占有率（百分比）。

```html
<div class="chart-box" id="chart-trend" style="height:320px;"></div>
```

```javascript
(function () {
  var dom = document.getElementById('chart-trend');
  if (!dom) return;
  var chart = echarts.init(dom);

  var months = ['2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
                '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12'];
  var volume   = [8619, 8875, 10299, 10016, 10462, 10478, 15298, 12859, 12303, 15324, 19014, 17517];
  var imprRate = [89.46, 88.49, 87.15, 83.91, 86.28, 90.65, 89.36, 93.12, 95.38, 96.19, 96.16, 95.04];
  var buyRate  = [99.71, 99.28, 98.46, 99.23, 99.05, 99.32, 99.21, 99.80, 99.80, 99.63, 99.43, 99.30];

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: Object.assign(tooltipStyle(), {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: C.border } },
      formatter: function (params) {
        var i = params[0].dataIndex;
        return '<b>' + months[i] + '</b><br/>'
          + '月搜索量：' + volume[i].toLocaleString() + '<br/>'
          + '<span style="color:' + C.tealDeep + '">曝光占有率：' + imprRate[i].toFixed(2) + '%</span><br/>'
          + '<span style="color:' + C.orange + '">购买占有率：' + buyRate[i].toFixed(2) + '%</span>';
      }
    }),
    legend: {
      data: ['曝光占有率', '购买占有率'],
      top: 6, right: 12,
      textStyle: { color: C.muted, fontSize: 12 }
    },
    grid: { left: 58, right: 78, top: 56, bottom: 52 },
    xAxis: Object.assign(axisStyle(), {
      type: 'category', data: months,
      axisLabel: { color: C.muted, fontSize: 10, rotate: 45, interval: 0 }
    }),
    yAxis: [
      Object.assign(axisStyle(), {
        type: 'value', name: '占有率',
        nameTextStyle: { color: C.tealDeep, fontSize: 11 },
        axisLabel: { color: C.muted, formatter: '{value}%' }
      }),
      {
        type: 'value', name: '月搜索量',
        nameTextStyle: { color: C.muted, fontSize: 11 },
        axisLine: { show: false }, axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: C.muted, fontSize: 10,
          formatter: function (v) {
            return v >= 1000000 ? (v/1000000).toFixed(1) + 'M'
              : v >= 1000 ? (v/1000).toFixed(0) + 'K' : v;
          }
        }
      }
    ],
    series: [
      {
        name: '月搜索量', type: 'bar', yAxisIndex: 1,
        data: volume,
        itemStyle: { color: 'rgba(94,138,135,0.14)' },
        barWidth: '55%', z: 1, silent: true
      },
      {
        name: '曝光占有率', type: 'line', yAxisIndex: 0,
        data: imprRate,
        smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: C.tealDeep, width: 2.8 },
        itemStyle: { color: C.tealDeep },
        endLabel: {
          show: true, color: C.tealDeep, fontWeight: 'bold', fontSize: 12, distance: 8,
          formatter: function (p) { return p.value.toFixed(1) + '%'; }
        },
        z: 5
      },
      {
        name: '购买占有率', type: 'line', yAxisIndex: 0,
        data: buyRate,
        smooth: true, symbol: 'diamond', symbolSize: 8,
        lineStyle: { color: C.orange, width: 2.8 },
        itemStyle: { color: C.orange },
        endLabel: {
          show: true, color: C.orange, fontWeight: 'bold', fontSize: 12, distance: 8,
          formatter: function (p) { return p.value.toFixed(1) + '%'; }
        },
        z: 5
      }
    ]
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

**关键细节**：
- 柱子用 `rgba(94,138,135,0.14)` 半透明做背景，不抢视觉；折线才是主角
- `endLabel` 在折线末端显示最新数值
- symbol 用 `'circle'` 和 `'diamond'` 区分两条线
- `z: 1`（柱）vs `z: 5`（线）确保折线在上层

---

## 4. 环形饼图（构成占比）

**适用**：展示整体的构成（如广告花费分布、流量来源占比）。

```html
<div class="chart-box" id="chart-composition" style="height:280px;"></div>
```

```javascript
(function () {
  var dom = document.getElementById('chart-composition');
  if (!dom) return;
  var chart = echarts.init(dom);

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: Object.assign(tooltipStyle(), {
      trigger: 'item',
      formatter: function (p) {
        return '<b>' + p.name + '</b><br/>¥' + p.value.toFixed(1) + '万（' + p.percent.toFixed(1) + '%）';
      }
    }),
    series: [{
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['50%', '52%'],
      padAngle: 2,
      itemStyle: { borderRadius: 4 },
      label: {
        formatter: function (p) { return p.name + '\n¥' + p.value.toFixed(1) + '万'; },
        fontSize: 11, lineHeight: 16, color: C.slate
      },
      data: [
        { value: 347.3, name: 'PPC',        itemStyle: { color: C.tealDeep } },
        { value: 15.3,  name: 'DSP Router', itemStyle: { color: C.tealMid } },
        { value: 7.4,   name: 'DSP KVM',    itemStyle: { color: C.gold } }
      ]
    }]
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

**关键细节**：
- `radius: ['48%', '72%']` 做环形（实心饼把内径改成 0 或去掉第一个值）
- `padAngle: 2` + `borderRadius: 4` 让各段之间有呼吸空隙
- 每个扇区用 `itemStyle.color` 独立上色（按语义分配 C 对象色）

**配色分配建议**：
- 主项（最大占比） → `C.tealDeep` 或 `C.teal`
- 次项 → `C.tealMid` 或 `C.sage`
- 小项/异类 → `C.gold` / `C.orange`
- 最多 5 段，超过合并为"其他"

---

## 5. 堆积柱图（多维度叠加）

**适用**：展示一批类目里多个组成部分的堆叠（如按来源/按层级）。

```html
<div class="chart-box" id="chart-stacked" style="height:340px;"></div>
```

```javascript
(function () {
  var dom = document.getElementById('chart-stacked');
  if (!dom) return;
  var chart = echarts.init(dom);

  var quarters = ['2025 Q1', '2025 Q2', '2025 Q3', '2025 Q4', '2026 Q1'];
  var ppc        = [245.1, 268.7, 291.2, 315.4, 347.3];
  var dspRouter  = [10.2, 12.1, 13.5, 14.8, 15.3];
  var dspKvm     = [5.1, 5.8, 6.2, 7.0, 7.4];

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: Object.assign(tooltipStyle(), {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (params) {
        var html = '<b>' + params[0].name + '</b><br/>';
        var total = 0;
        params.forEach(function (p) {
          html += p.marker + p.seriesName + '：¥' + p.value.toFixed(1) + '万<br/>';
          total += p.value;
        });
        html += '<hr style="border:0;border-top:1px solid rgba(255,255,255,0.2);margin:6px 0"/>';
        html += '<b>合计：¥' + total.toFixed(1) + '万</b>';
        return html;
      }
    }),
    legend: {
      data: ['PPC', 'DSP Router', 'DSP KVM'],
      top: 6, textStyle: { color: C.muted, fontSize: 12 }
    },
    grid: { left: 56, right: 24, top: 44, bottom: 28 },
    xAxis: {
      type: 'category', data: quarters,
      axisLabel: { color: C.slate, fontSize: 12, fontWeight: 'bold' },
      axisLine: { lineStyle: { color: C.border } }, axisTick: { show: false }
    },
    yAxis: Object.assign(axisStyle(), {
      type: 'value',
      axisLabel: { color: C.muted, formatter: '¥{value}万' }
    }),
    series: [
      {
        name: 'PPC', type: 'bar', stack: 'total', barWidth: '48%',
        itemStyle: { color: C.tealDeep },
        data: ppc
      },
      {
        name: 'DSP Router', type: 'bar', stack: 'total',
        itemStyle: { color: C.tealMid },
        data: dspRouter
      },
      {
        name: 'DSP KVM', type: 'bar', stack: 'total',
        itemStyle: { color: C.gold },
        data: dspKvm,
        label: {
          show: true, position: 'top',
          formatter: function (p) {
            return '¥' + (ppc[p.dataIndex] + dspRouter[p.dataIndex] + dspKvm[p.dataIndex]).toFixed(0) + '万';
          },
          fontSize: 11, fontWeight: 'bold', color: C.slate
        }
      }
    ]
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

**关键细节**：
- 所有 series 设 `stack: 'total'`（相同 stack key）即可堆叠
- 只在最顶层 series 加 `label.position: 'top'` 显示总和
- 颜色从深到浅按语义层级分配（主项→tealDeep，次项→tealMid，异类/警示→gold）

---

## 通用优化建议

### 初始化模式

所有图表都用 IIFE 包裹避免污染全局：

```javascript
(function () {
  var dom = document.getElementById('chart-xxx');
  if (!dom) return;
  var chart = echarts.init(dom);
  chart.setOption({ /* ... */ });
  window.addEventListener('resize', function () { chart.resize(); });
})();
```

### 数字格式化

统一用 `toLocaleString()` 加千分位：
```javascript
value.toLocaleString()           // 1,234,567
(v/1e6).toFixed(2) + 'M'         // 1.23M
(v/1e3).toFixed(0) + 'K'         // 123K
'¥' + (v/1e4).toFixed(1) + '万'   // ¥123.4万
```

### 坐标轴尺寸

- `grid: { left: 56-80, right: 16-80, top: 16-56, bottom: 28-60 }`
- 带 y 轴 name 的要留 `top: 44-56` 给 name
- 带 legend 的要再往下 `top: 56+`
- 横向柱图 `right` 要给数值 label 留空间（通常 130+）

### 响应式

所有图表都应该在 `window.resize` 时调用 `chart.resize()`。模板已经写好，不要漏掉。

### 可访问性

不要把数值差异仅仅靠颜色传达——同时用 label（文字标注）+ 颜色才是无障碍设计。
