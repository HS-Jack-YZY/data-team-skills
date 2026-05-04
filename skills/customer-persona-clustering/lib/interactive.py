"""Stage 9 — 自包含交互可视化 HTML.

读 Stage 4-6 的产物 (clusters.parquet / meta_ward_labels.json / ward_linkage.npy /
umap_nd.npy), 渲染成单文件 HTML 给业务/产品方探索:

  ① 客户地图 (UMAP 散点) — Z 选 "无" = 2D, 选维度自动 3D, 拖拽旋转 + 滚轮缩放.
     悬浮任意点 → 标签 + 原评论
  ② 客户分群层级树 (Ward dendrogram) — 鼠标垂直移动选不同分群粒度,
     右下方面板实时显示该粒度下每组业务命名 + 人数 + 来自的原始小群

无外部 CDN 依赖 (纯 SVG + vanilla JS), 离线可看.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram


def build_interactive_html(cfg: dict, out_dir: Path) -> Path:
    """Read pipeline outputs from out_dir, write interactive.html, return its path.

    Required files in out_dir:
      - clusters.parquet (cols: umap_2d_x, umap_2d_y, hdbscan_id, body, ward_meta_*, ...)
      - meta_ward_labels.json  (Stage 6 output)
      - ward_linkage.npy       (Stage 5 output)
      - umap_nd.npy            (Stage 4 output, used to embed 10D coords for X/Y/Z 选轴)
    """
    out_dir = Path(out_dir)

    df = pd.read_parquet(out_dir / "clusters.parquet")
    labels = json.loads((out_dir / "meta_ward_labels.json").read_text())
    Z = np.load(out_dir / "ward_linkage.npy")
    coords_nd = np.load(out_dir / "umap_nd.npy")
    if coords_nd.shape[0] != len(df):
        raise RuntimeError(
            f"umap_nd.npy 行数 {coords_nd.shape[0]} 与 clusters.parquet 行数 {len(df)} 不一致, "
            "可能 stage 4 / 5 / 6 之间状态不同步, 请重跑或部分重跑"
        )
    nd_dim = coords_nd.shape[1]

    text_col = cfg.get("text_column", "body")

    # ---- scatter points (含 2D + 10D 全部坐标) -----------------------------
    scatter = []
    for i, (_, r) in enumerate(df.iterrows()):
        scatter.append({
            "x": float(r["umap_2d_x"]),
            "y": float(r["umap_2d_y"]),
            "nd": [float(v) for v in coords_nd[i]],
            "hid": int(r["hdbscan_id"]),
            "body": (str(r.get(text_col, "") or "")[:600]).strip(),
        })

    # ---- dendrogram coords -------------------------------------------------
    ddata = dendrogram(Z, no_plot=True, color_threshold=-1)
    icoord = [[float(x) for x in row] for row in ddata["icoord"]]
    dcoord = [[float(y) for y in row] for row in ddata["dcoord"]]
    leaves = [int(x) for x in ddata["leaves"]]

    # ---- k -> height range -------------------------------------------------
    n = Z.shape[0] + 1
    merge_heights = sorted(Z[:, 2].tolist())
    k_to_height: dict[int, list[float]] = {}
    for k in range(2, n + 1):
        if k == n:
            lower, upper = 0.0, merge_heights[0]
        else:
            lower = merge_heights[n - k - 1]
            upper = (
                merge_heights[n - k]
                if n - k < len(merge_heights)
                else merge_heights[-1] + 1.0
            )
        k_to_height[k] = [float(lower), float(upper)]

    # ---- k -> labelled clusters --------------------------------------------
    k_labels: dict[int, list[dict]] = {}
    for k_str, entry in labels["by_k"].items():
        k = int(k_str.split("=")[1])
        k_labels[k] = sorted(
            [
                {
                    "id": int(item["id"]),
                    "name": item["name"],
                    "size": int(item["size"]),
                    "members": [int(m) for m in item["hdbscan_members"]],
                }
                for item in entry["labels"]
            ],
            key=lambda x: -x["size"],
        )

    # ---- leaf info for x-axis (scipy convention: leaf x = 5 + 10*i) --------
    hdbscan_sizes = (
        df[df["hdbscan_id"] != -1]["hdbscan_id"].value_counts().to_dict()
    )
    leaf_info = [
        {"id": int(leaf_id), "size": int(hdbscan_sizes.get(leaf_id, 0)), "x": 5.0 + 10.0 * i}
        for i, leaf_id in enumerate(leaves)
    ]

    # ---- pick a sensible default highlight k -------------------------------
    levels_highlight = labels.get("levels_highlight", [])
    valid_levels = [k for k in levels_highlight if k in k_labels]
    if valid_levels:
        default_k = valid_levels[len(valid_levels) // 2]
    elif k_labels:
        default_k = sorted(k_labels.keys())[len(k_labels) // 2]
    else:
        default_k = 2

    data = {
        "product_name": cfg.get("product_name", "通用产品"),
        "n_total": len(df),
        "n_noise": int((df["hdbscan_id"] == -1).sum()),
        "n_leaves": n,
        "nd_dim": nd_dim,
        "scatter": scatter,
        "dendrogram": {
            "icoord": icoord,
            "dcoord": dcoord,
            "leaves": leaves,
            "leaf_info": leaf_info,
        },
        "k_to_height": {str(k): v for k, v in k_to_height.items()},
        "k_labels": {str(k): v for k, v in k_labels.items()},
        "k_labeled": labels["k_labeled"],
        "levels_highlight": levels_highlight,
        "default_k": default_k,
    }

    html = _HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out_path = out_dir / "interactive.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<title>客户画像聚类 — 交互可视化</title>
<style>
  body { font-family: -apple-system, "PingFang SC", "Segoe UI", sans-serif;
         margin: 0; padding: 20px; background: #fafafa; color: #222; }
  h1 { font-size: 18px; margin: 0 0 6px 0; }
  .meta { font-size: 12px; color: #666; margin-bottom: 18px; }
  .container { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 1200px) { .container { grid-template-columns: 1fr; } }
  .panel { background: white; border: 1px solid #e0e0e0; border-radius: 8px;
           padding: 16px; }
  .panel h2 { font-size: 14px; margin: 0 0 8px 0; color: #444; }
  .controls { font-size: 12px; margin-bottom: 8px; color: #555; }
  .controls select { font-size: 12px; padding: 2px 6px; }
  svg { display: block; max-width: 100%; height: auto; }

  #tip { position: fixed; pointer-events: none;
         background: rgba(20,20,20,0.95); color: white; font-size: 11px;
         padding: 10px 12px; border-radius: 4px; max-width: 380px;
         line-height: 1.5; z-index: 999; display: none;
         box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
  #tip .tlabel { font-weight: 600; color: #ffd54f; margin-bottom: 4px;
                  font-size: 12px; }
  #tip .tmeta { color: #aaa; font-size: 10px; margin-bottom: 6px; }
  #tip .tbody { color: #ddd; font-size: 11px; white-space: pre-wrap;
                word-break: break-word; }

  .pt { stroke: rgba(255,255,255,0.6); stroke-width: 0.5; cursor: pointer; }
  .pt.noise { fill: #cfcfcf; }
  .pt:hover { stroke: #000; stroke-width: 2; }
  svg#scatter.mode3d { cursor: grab; }
  svg#scatter.mode3d.dragging { cursor: grabbing; }
  svg#scatter.mode3d .pt { cursor: grab; }
  svg#scatter.mode3d.dragging .pt { pointer-events: none; }

  .dgline { fill: none; stroke: #555; stroke-width: 1.4; }
  .cutline { stroke: #e53935; stroke-width: 2;
             stroke-dasharray: 4 3; pointer-events: none; }
  .cutarea { fill: transparent; cursor: ns-resize; }

  #klabels { margin-top: 10px; padding: 10px 12px; background: #f7f7f7;
             border-radius: 4px; min-height: 110px; font-size: 12px;
             line-height: 1.7; }
  #klabels .ktitle { font-weight: 600; color: #d32f2f; margin-bottom: 6px;
                     font-size: 13px; }
  #klabels .row { display: flex; align-items: flex-start; gap: 6px;
                  margin: 2px 0; }
  #klabels .swatch { width: 12px; height: 12px; border-radius: 2px;
                     flex: 0 0 12px; margin-top: 4px; }
  #klabels .name { font-weight: 600; }
  #klabels .meta-info { color: #666; margin-left: 4px; font-size: 11px; }

  .legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;
            font-size: 11px; padding: 8px; background: #f7f7f7;
            border-radius: 4px; }
  .legend .item { display: flex; align-items: center; gap: 5px; }
  .legend .swatch { width: 11px; height: 11px; border-radius: 2px; }
</style>
</head>
<body>
<h1>客户画像聚类 — 交互可视化</h1>
<div class="meta" id="meta"></div>

<div class="container">
  <div class="panel">
    <h2>① 客户地图 — 鼠标悬浮看原评论 · Z 选「无」是 2D, 选任何特征轴自动切 3D</h2>
    <div class="controls" style="line-height:1.9">
      分群粒度: <select id="kSel"></select>
      <span style="margin-left:14px;color:#888">边缘客户 = 灰色</span>
      <br>
      X: <select id="xDimSel"></select>
      &nbsp;Y: <select id="yDimSel"></select>
      &nbsp;Z: <select id="zDimSel"></select>
      <span style="margin-left:10px;color:#888;font-size:11px">
        主视图 = 给人眼看的简化 2D 布局；特征轴 1-N = 算法实际用来分群的抽象差异维度；3D 可拖拽旋转 / 滚轮缩放
      </span>
    </div>
    <svg id="scatter" viewBox="0 0 600 500" width="600" height="500" style="user-select:none"></svg>
    <div class="legend" id="scatLegend"></div>
  </div>

  <div class="panel">
    <h2>② 客户分群层级树 — 鼠标在树上垂直移动看不同分群粒度</h2>
    <div class="controls">
      <span id="dgKtitle">将鼠标移到下方树图区域</span>
    </div>
    <svg id="dgram" viewBox="0 0 600 500" width="600" height="500"></svg>
    <div id="klabels">
      <span class="ktitle">将鼠标移到树图上, 不同高度对应不同的分群粒度 (越高分得越粗)</span>
    </div>
  </div>
</div>

<div id="tip"></div>

<script>const DATA = __DATA__;</script>
<script>
const SVG_NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tip");

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}
function showTip(html, evt) {
  tip.innerHTML = html;
  tip.style.display = "block";
  const x = evt.clientX + 14, y = evt.clientY + 14;
  tip.style.left = Math.min(x, window.innerWidth - 400) + "px";
  tip.style.top = Math.min(y, window.innerHeight - tip.offsetHeight - 12) + "px";
}
function hideTip() { tip.style.display = "none"; }

const PALETTE = [
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
  "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
];
function colorFor(id) { return PALETTE[(id - 1 + PALETTE.length) % PALETTE.length]; }

document.getElementById("meta").textContent =
  `${DATA.product_name} · 共 ${DATA.n_total} 条客户画像 · ` +
  `自动识别 ${DATA.n_leaves} 个原始小群 · ${DATA.n_noise} 条边缘客户 · ` +
  `可选分群粒度 = ${DATA.k_labeled.join(", ")} 组`;

const scatSvg = document.getElementById("scatter");
const W = 600, H = 500, M = 32;

const AXIS_OPTS = [
  {key: "2d_x", label: "主视图 · 横向"},
  {key: "2d_y", label: "主视图 · 纵向"},
];
for (let i = 0; i < DATA.nd_dim; i++) {
  AXIS_OPTS.push({key: "nd_" + i, label: `特征轴 ${i + 1}`});
}

function getAxis(p, key) {
  if (key === "2d_x") return p.x;
  if (key === "2d_y") return p.y;
  if (key.startsWith("nd_")) return p.nd[parseInt(key.slice(3), 10)];
  return 0;
}

const kSel = document.getElementById("kSel");
DATA.k_labeled.forEach(k => {
  const o = document.createElement("option");
  o.value = String(k);
  o.textContent = `分成 ${k} 组`;
  if (k === DATA.default_k) o.selected = true;
  kSel.appendChild(o);
});

const xDimSel = document.getElementById("xDimSel");
const yDimSel = document.getElementById("yDimSel");
const zDimSel = document.getElementById("zDimSel");

const zNone = document.createElement("option");
zNone.value = "__none__";
zNone.textContent = "无 (2D 模式)";
zNone.selected = true;
zDimSel.appendChild(zNone);

AXIS_OPTS.forEach(opt => {
  const ox = document.createElement("option"); ox.value = opt.key; ox.textContent = opt.label;
  const oy = document.createElement("option"); oy.value = opt.key; oy.textContent = opt.label;
  const oz = document.createElement("option"); oz.value = opt.key; oz.textContent = opt.label;
  if (opt.key === "2d_x") ox.selected = true;
  if (opt.key === "2d_y") oy.selected = true;
  xDimSel.appendChild(ox); yDimSel.appendChild(oy); zDimSel.appendChild(oz);
});

function renderScatter(k, xKey, yKey) {
  const labelByHid = {};
  DATA.k_labels[k].forEach(entry => {
    entry.members.forEach(hid => { labelByHid[hid] = entry; });
  });

  const xv = DATA.scatter.map(p => getAxis(p, xKey));
  const yv = DATA.scatter.map(p => getAxis(p, yKey));
  const xMin = Math.min(...xv), xMax = Math.max(...xv);
  const yMin = Math.min(...yv), yMax = Math.max(...yv);
  const xRange = (xMax - xMin) || 1;
  const yRange = (yMax - yMin) || 1;
  const sx = v => M + (v - xMin) / xRange * (W - 2 * M);
  const sy = v => H - M - (v - yMin) / yRange * (H - 2 * M);

  scatSvg.innerHTML = "";

  const bg = document.createElementNS(SVG_NS, "rect");
  bg.setAttribute("x", M); bg.setAttribute("y", M);
  bg.setAttribute("width", W - 2 * M); bg.setAttribute("height", H - 2 * M);
  bg.setAttribute("fill", "#fafafa");
  bg.setAttribute("stroke", "#eee");
  scatSvg.appendChild(bg);

  const xLab = document.createElementNS(SVG_NS, "text");
  xLab.setAttribute("x", W / 2); xLab.setAttribute("y", H - 8);
  xLab.setAttribute("text-anchor", "middle"); xLab.setAttribute("font-size", "10");
  xLab.setAttribute("fill", "#888");
  xLab.textContent = AXIS_OPTS.find(o => o.key === xKey).label;
  scatSvg.appendChild(xLab);
  const yLab = document.createElementNS(SVG_NS, "text");
  yLab.setAttribute("x", 12); yLab.setAttribute("y", H / 2);
  yLab.setAttribute("text-anchor", "middle"); yLab.setAttribute("font-size", "10");
  yLab.setAttribute("fill", "#888");
  yLab.setAttribute("transform", `rotate(-90 12 ${H / 2})`);
  yLab.textContent = AXIS_OPTS.find(o => o.key === yKey).label;
  scatSvg.appendChild(yLab);

  const order = [...DATA.scatter].sort((a, b) =>
    (a.hid === -1 ? 0 : 1) - (b.hid === -1 ? 0 : 1));

  order.forEach(p => {
    const c = document.createElementNS(SVG_NS, "circle");
    c.setAttribute("cx", sx(getAxis(p, xKey)));
    c.setAttribute("cy", sy(getAxis(p, yKey)));
    c.setAttribute("r", 4.5);
    if (p.hid === -1) {
      c.setAttribute("class", "pt noise");
      c.setAttribute("fill-opacity", "0.45");
    } else {
      const lbl = labelByHid[p.hid];
      c.setAttribute("class", "pt");
      c.setAttribute("fill", lbl ? colorFor(lbl.id) : "#999");
    }

    c.addEventListener("mouseenter", e => {
      const lbl = p.hid === -1 ? null : labelByHid[p.hid];
      const labelText = lbl ? lbl.name : (p.hid === -1 ? "边缘客户" : "未命名");
      const meta = `原始小群 #${p.hid}` + (lbl ? ` · 该组共 ${lbl.size} 人` : " · 边缘客户");
      const body = p.body || "(空)";
      const html = `<div class="tlabel">${escapeHtml(labelText)}</div>` +
                   `<div class="tmeta">${escapeHtml(meta)}</div>` +
                   `<div class="tbody">${escapeHtml(body)}</div>`;
      showTip(html, e);
    });
    c.addEventListener("mousemove", e => {
      const x = e.clientX + 14, y = e.clientY + 14;
      tip.style.left = Math.min(x, window.innerWidth - 400) + "px";
      tip.style.top = Math.min(y, window.innerHeight - tip.offsetHeight - 12) + "px";
    });
    c.addEventListener("mouseleave", hideTip);
    scatSvg.appendChild(c);
  });

  buildLegend(k);
}

let theta_x = -0.35;
let theta_y = 0.55;
let zoom3d = 1.0;
let dragging = false;
let lastMouse = {x: 0, y: 0};

function project3D(x, y, z) {
  const cy = Math.cos(theta_y), sy_ = Math.sin(theta_y);
  const x1 = x * cy + z * sy_;
  const z1 = -x * sy_ + z * cy;
  const cx = Math.cos(theta_x), sx_ = Math.sin(theta_x);
  const y2 = y * cx - z1 * sx_;
  const z2 = y * sx_ + z1 * cx;
  return {sx: x1, sy: y2, depth: z2};
}

function renderScatter3D(k, xKey, yKey, zKey) {
  const labelByHid = {};
  DATA.k_labels[k].forEach(entry => {
    entry.members.forEach(hid => { labelByHid[hid] = entry; });
  });

  const xs = DATA.scatter.map(p => getAxis(p, xKey));
  const ys = DATA.scatter.map(p => getAxis(p, yKey));
  const zs = DATA.scatter.map(p => getAxis(p, zKey));
  const cx_w = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy_w = (Math.min(...ys) + Math.max(...ys)) / 2;
  const cz_w = (Math.min(...zs) + Math.max(...zs)) / 2;
  const span = Math.max(
    Math.max(...xs) - Math.min(...xs),
    Math.max(...ys) - Math.min(...ys),
    Math.max(...zs) - Math.min(...zs),
  ) || 1;
  const SCALE = (Math.min(W, H) - 2 * M) * 0.45 * zoom3d / (span / 2);
  const SCREEN_CX = W / 2, SCREEN_CY = H / 2;

  const projected = DATA.scatter.map(p => {
    const proj = project3D(
      getAxis(p, xKey) - cx_w,
      getAxis(p, yKey) - cy_w,
      getAxis(p, zKey) - cz_w,
    );
    return {
      p: p,
      sx: SCREEN_CX + proj.sx * SCALE,
      sy: SCREEN_CY - proj.sy * SCALE,
      depth: proj.depth,
    };
  });
  projected.sort((a, b) => a.depth - b.depth);

  scatSvg.innerHTML = "";

  const bg = document.createElementNS(SVG_NS, "rect");
  bg.setAttribute("x", M); bg.setAttribute("y", M);
  bg.setAttribute("width", W - 2 * M); bg.setAttribute("height", H - 2 * M);
  bg.setAttribute("fill", "#fafafa");
  bg.setAttribute("stroke", "#eee");
  scatSvg.appendChild(bg);

  const COMPASS_CX = M + 30, COMPASS_CY = H - M - 30, COMPASS_R = 22;
  const axes = [
    {dir: [1, 0, 0], color: "#d62728", label: "X"},
    {dir: [0, 1, 0], color: "#2ca02c", label: "Y"},
    {dir: [0, 0, 1], color: "#1f77b4", label: "Z"},
  ];
  axes.forEach(ax => {
    const proj = project3D(ax.dir[0], ax.dir[1], ax.dir[2]);
    const ex = COMPASS_CX + proj.sx * COMPASS_R;
    const ey = COMPASS_CY - proj.sy * COMPASS_R;
    const ln = document.createElementNS(SVG_NS, "line");
    ln.setAttribute("x1", COMPASS_CX); ln.setAttribute("y1", COMPASS_CY);
    ln.setAttribute("x2", ex); ln.setAttribute("y2", ey);
    ln.setAttribute("stroke", ax.color); ln.setAttribute("stroke-width", "1.6");
    scatSvg.appendChild(ln);
    const t = document.createElementNS(SVG_NS, "text");
    t.setAttribute("x", ex); t.setAttribute("y", ey - 2);
    t.setAttribute("text-anchor", "middle"); t.setAttribute("font-size", "9");
    t.setAttribute("fill", ax.color);
    t.textContent = ax.label;
    scatSvg.appendChild(t);
  });

  const hint = document.createElementNS(SVG_NS, "text");
  hint.setAttribute("x", W - M); hint.setAttribute("y", M + 12);
  hint.setAttribute("text-anchor", "end"); hint.setAttribute("font-size", "10");
  hint.setAttribute("fill", "#999");
  hint.textContent = "拖动旋转 · 滚轮缩放";
  scatSvg.appendChild(hint);

  const xLab = document.createElementNS(SVG_NS, "text");
  xLab.setAttribute("x", M + 60); xLab.setAttribute("y", H - 6);
  xLab.setAttribute("font-size", "10"); xLab.setAttribute("fill", "#888");
  xLab.textContent = `X=${AXIS_OPTS.find(o => o.key === xKey).label}  Y=${AXIS_OPTS.find(o => o.key === yKey).label}  Z=${AXIS_OPTS.find(o => o.key === zKey).label}`;
  scatSvg.appendChild(xLab);

  projected.forEach(({p, sx: ssx, sy: ssy, depth}) => {
    const c = document.createElementNS(SVG_NS, "circle");
    c.setAttribute("cx", ssx); c.setAttribute("cy", ssy);
    const depthNorm = depth / (span * 0.5 + 1e-9);
    const r = Math.max(2.2, 4.2 + depthNorm * 1.6);
    c.setAttribute("r", r);
    c.setAttribute("fill-opacity", Math.max(0.4, 0.85 + depthNorm * 0.15));

    if (p.hid === -1) {
      c.setAttribute("class", "pt noise");
    } else {
      const lbl = labelByHid[p.hid];
      c.setAttribute("class", "pt");
      c.setAttribute("fill", lbl ? colorFor(lbl.id) : "#999");
    }

    c.addEventListener("mouseenter", e => {
      if (dragging) return;
      const lbl = p.hid === -1 ? null : labelByHid[p.hid];
      const labelText = lbl ? lbl.name : (p.hid === -1 ? "边缘客户" : "未命名");
      const meta = `原始小群 #${p.hid}` + (lbl ? ` · 该组共 ${lbl.size} 人` : " · 边缘客户");
      const body = p.body || "(空)";
      const html = `<div class="tlabel">${escapeHtml(labelText)}</div>` +
                   `<div class="tmeta">${escapeHtml(meta)}</div>` +
                   `<div class="tbody">${escapeHtml(body)}</div>`;
      showTip(html, e);
    });
    c.addEventListener("mousemove", e => {
      if (dragging) return;
      const x = e.clientX + 14, y = e.clientY + 14;
      tip.style.left = Math.min(x, window.innerWidth - 400) + "px";
      tip.style.top = Math.min(y, window.innerHeight - tip.offsetHeight - 12) + "px";
    });
    c.addEventListener("mouseleave", hideTip);
    scatSvg.appendChild(c);
  });

  buildLegend(k);
}

function buildLegend(k) {
  const leg = document.getElementById("scatLegend");
  leg.innerHTML = "";
  DATA.k_labels[k].forEach(entry => {
    const item = document.createElement("span");
    item.className = "item";
    item.innerHTML = `<span class="swatch" style="background:${colorFor(entry.id)}"></span>` +
                     `${escapeHtml(entry.name)} <span style="color:#666">(${entry.size})</span>`;
    leg.appendChild(item);
  });
  if (DATA.n_noise > 0) {
    const item = document.createElement("span");
    item.className = "item";
    item.innerHTML = `<span class="swatch" style="background:#cfcfcf"></span>边缘客户 (${DATA.n_noise})`;
    leg.appendChild(item);
  }
}

function isMode3D() { return zDimSel.value !== "__none__"; }

scatSvg.addEventListener("mousedown", e => {
  if (!isMode3D()) return;
  dragging = true;
  scatSvg.classList.add("dragging");
  lastMouse = {x: e.clientX, y: e.clientY};
  hideTip();
  e.preventDefault();
});
window.addEventListener("mousemove", e => {
  if (!dragging) return;
  const dx = e.clientX - lastMouse.x;
  const dy = e.clientY - lastMouse.y;
  theta_y += dx * 0.008;
  theta_x += dy * 0.008;
  theta_x = Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, theta_x));
  lastMouse = {x: e.clientX, y: e.clientY};
  rerender();
});
window.addEventListener("mouseup", () => {
  if (!dragging) return;
  dragging = false;
  scatSvg.classList.remove("dragging");
});
scatSvg.addEventListener("wheel", e => {
  if (!isMode3D()) return;
  e.preventDefault();
  zoom3d *= e.deltaY < 0 ? 1.1 : 1 / 1.1;
  zoom3d = Math.max(0.2, Math.min(5, zoom3d));
  rerender();
}, {passive: false});

function rerender() {
  const k = parseInt(kSel.value, 10);
  if (isMode3D()) {
    scatSvg.classList.add("mode3d");
    renderScatter3D(k, xDimSel.value, yDimSel.value, zDimSel.value);
  } else {
    scatSvg.classList.remove("mode3d");
    renderScatter(k, xDimSel.value, yDimSel.value);
  }
}
rerender();
[kSel, xDimSel, yDimSel, zDimSel].forEach(el => el.addEventListener("change", rerender));

// ---- Dendrogram ----
const dgSvg = document.getElementById("dgram");
const DG_W = 600, DG_H = 500;
const DG_TOP = 30, DG_BOT = 90, DG_L = 60, DG_R = 30;
const dg = DATA.dendrogram;
const allX = dg.icoord.flat();
const allY = dg.dcoord.flat();
const dgxMax = Math.max(...allX);
const dgyMax = Math.max(...allY) * 1.05;

function dx(x) { return DG_L + x / dgxMax * (DG_W - DG_L - DG_R); }
function dy(y) { return DG_H - DG_BOT - y / dgyMax * (DG_H - DG_TOP - DG_BOT); }
function invertDy(yPx) {
  return (DG_H - DG_BOT - yPx) * dgyMax / (DG_H - DG_TOP - DG_BOT);
}

dgSvg.innerHTML = "";

const yAxis = document.createElementNS(SVG_NS, "line");
yAxis.setAttribute("x1", DG_L); yAxis.setAttribute("x2", DG_L);
yAxis.setAttribute("y1", dy(0)); yAxis.setAttribute("y2", dy(dgyMax));
yAxis.setAttribute("stroke", "#bbb");
yAxis.setAttribute("stroke-width", "0.8");
dgSvg.appendChild(yAxis);

for (let i = 0; i <= 5; i++) {
  const v = dgyMax * i / 5;
  const t = document.createElementNS(SVG_NS, "text");
  t.setAttribute("x", DG_L - 6); t.setAttribute("y", dy(v) + 3);
  t.setAttribute("text-anchor", "end");
  t.setAttribute("font-size", "9");
  t.setAttribute("fill", "#888");
  t.textContent = v.toFixed(2);
  dgSvg.appendChild(t);
  const g = document.createElementNS(SVG_NS, "line");
  g.setAttribute("x1", DG_L); g.setAttribute("x2", DG_W - DG_R);
  g.setAttribute("y1", dy(v)); g.setAttribute("y2", dy(v));
  g.setAttribute("stroke", "#eee");
  g.setAttribute("stroke-width", "0.5");
  dgSvg.appendChild(g);
}

dg.icoord.forEach((xs, i) => {
  const ys = dg.dcoord[i];
  const d = `M ${dx(xs[0])} ${dy(ys[0])} L ${dx(xs[1])} ${dy(ys[1])} ` +
            `L ${dx(xs[2])} ${dy(ys[2])} L ${dx(xs[3])} ${dy(ys[3])}`;
  const p = document.createElementNS(SVG_NS, "path");
  p.setAttribute("d", d);
  p.setAttribute("class", "dgline");
  dgSvg.appendChild(p);
});

dg.leaf_info.forEach(leaf => {
  const lx = dx(leaf.x);
  const ly = dy(0) + 12;
  const t = document.createElementNS(SVG_NS, "text");
  t.setAttribute("x", lx); t.setAttribute("y", ly);
  t.setAttribute("text-anchor", "end");
  t.setAttribute("font-size", "10");
  t.setAttribute("fill", "#555");
  t.setAttribute("transform", `rotate(-50 ${lx} ${ly})`);
  t.textContent = `小群${leaf.id} (${leaf.size}人)`;
  dgSvg.appendChild(t);
});

const yLab = document.createElementNS(SVG_NS, "text");
yLab.setAttribute("x", 14);
yLab.setAttribute("y", dy(dgyMax / 2));
yLab.setAttribute("text-anchor", "middle");
yLab.setAttribute("font-size", "10");
yLab.setAttribute("fill", "#666");
yLab.setAttribute("transform", `rotate(-90 14 ${dy(dgyMax / 2)})`);
yLab.textContent = "差异度 (越高 = 划分越粗)";
dgSvg.appendChild(yLab);

const cutline = document.createElementNS(SVG_NS, "line");
cutline.setAttribute("class", "cutline");
cutline.setAttribute("x1", DG_L);
cutline.setAttribute("x2", DG_W - DG_R);
cutline.setAttribute("y1", dy(dgyMax / 2));
cutline.setAttribute("y2", dy(dgyMax / 2));
cutline.style.display = "none";
dgSvg.appendChild(cutline);

const overlay = document.createElementNS(SVG_NS, "rect");
overlay.setAttribute("class", "cutarea");
overlay.setAttribute("x", DG_L);
overlay.setAttribute("y", dy(dgyMax));
overlay.setAttribute("width", DG_W - DG_L - DG_R);
overlay.setAttribute("height", dy(0) - dy(dgyMax));
dgSvg.appendChild(overlay);

const dgKtitle = document.getElementById("dgKtitle");
const klabelsBox = document.getElementById("klabels");

overlay.addEventListener("mousemove", e => {
  const rect = dgSvg.getBoundingClientRect();
  const scaleY = DG_H / rect.height;
  const yPx = (e.clientY - rect.top) * scaleY;
  const yVal = invertDy(yPx);

  if (yVal < 0 || yVal > dgyMax) return;

  cutline.style.display = "";
  cutline.setAttribute("y1", yPx);
  cutline.setAttribute("y2", yPx);

  let kMatch = null;
  for (const [kStr, range] of Object.entries(DATA.k_to_height)) {
    if (yVal > range[0] && yVal <= range[1]) { kMatch = parseInt(kStr, 10); break; }
  }
  if (kMatch === null && yVal <= 0) kMatch = DATA.n_leaves;

  if (kMatch != null && DATA.k_labels[kMatch]) {
    dgKtitle.textContent = `当前切到 ${kMatch} 组 (差异度 ≈ ${yVal.toFixed(3)})`;
    let html = `<div class="ktitle">分成 ${kMatch} 组</div>`;
    DATA.k_labels[kMatch].forEach(entry => {
      html += `<div class="row">` +
              `<span class="swatch" style="background:${colorFor(entry.id)}"></span>` +
              `<div><span class="name">${escapeHtml(entry.name)}</span>` +
              `<span class="meta-info">${entry.size} 人 · 来自小群 [${entry.members.join(", ")}]</span></div>` +
              `</div>`;
    });
    klabelsBox.innerHTML = html;
  } else {
    dgKtitle.textContent = `差异度 ≈ ${yVal.toFixed(3)} (此高度无对应分群)`;
  }
});
overlay.addEventListener("mouseleave", () => {
  cutline.style.display = "none";
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    # Standalone usage: python3 lib/interactive.py --config x.yaml
    import argparse
    import sys
    import yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="yaml 配置文件路径")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    out_dir = Path(cfg["output_dir"]).expanduser().resolve()
    if not out_dir.exists():
        sys.exit(f"✗ output_dir 不存在: {out_dir}")
    path = build_interactive_html(cfg, out_dir)
    print(f"✓ {path} ({path.stat().st_size / 1024:.1f} KB)")
