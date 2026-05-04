---
name: customer-persona-clustering
description: |
  从评论 / 反馈 / 论坛抓取数据中提取客户画像并多粒度聚类的完整流水线.
  通用产品适用 (路由器 / 厨具 / SaaS / 任何品类), 配置文件驱动.

  Ward 层级聚类生成全档 k=2..N 切刀, LLM 为每一档每个组业务命名,
  上一档命名作为下一档的 context, 跨档术语自动一致. 业务方按需选 k.

  - k=2/3: 老板视图 / 战略层
  - k=5/10/15: 业务报告 / PPT (config.levels 高亮档)
  - k=N: 长尾营销 / 小众 segment

  Trigger when:
  - 用户给一份 csv 评论/反馈数据, 要 "客户画像" / "用户分群" / "customer segments"
  - 用户提到 "找小众群体" / "看用户类型" / "feedback clustering"
  - 用户显式调用 /customer-persona-clustering
---

# Customer Persona Clustering

把任意产品的用户评论变成可操作的客户画像分群. 8 stage 流水线 + 全档 LLM 命名, 适用任何品类.

## 何时触发

- 用户给一个 CSV (评论 / 反馈 / 客服记录) 并要做"客户分类"或"用户画像"
- 用户要"看我们用户分几类"或"这堆评论里有什么人群"
- 用户说"用 X 这个 skill 处理这份数据"

不要触发:
- 仅做话题分析 (用户想知道"在聊什么"而不是"什么人在聊") → 用 BERTopic 或 c-TF-IDF 类工具
- 单条评论分类 → 直接 LLM tagging 即可
- 数据量 < 100 条 → 样本太少, 聚类不可靠

## 执行步骤

### 第 1 步: 读 config + 检查输入

读 `config.example.yaml` (用户应该 cp 一份到自己的项目目录改). 关键字段:

```yaml
product_name: "..."          # 用户产品名 (用于 prompt)
input_csv: "path/to/data.csv"
text_column: "review_text"   # 必填
optional_columns:            # 选填, 用于上下文树
  id: "review_id"
  parent_id: "parent_id"
  post_id: "post_id"
  title: "title"
output_dir: "./output"

embedding:
  provider: openai           # openai / voyage / gemini
  model: text-embedding-3-large
clustering:
  hdbscan:
    min_cluster_size: 8
meta_merge:
  ward:
    levels: [5, 10, 15, 20]  # report 详细展开的高亮档
  llm:
    max_k: null              # null = k=2..N 全档命名 (推荐)
```

### 第 2 步: 跑流水线

执行 `lib/pipeline.py`, 它依次做:
1. 加载 CSV + 噪声过滤 (短评论 / 模板复读 / 关键词排除)
2. **Persona 生成** (Claude): 用 `prompts/persona.md` 模板, 6 维结构化画像
3. **Embedding** (默认 OpenAI text-embedding-3-large)
4. **UMAP 降维** (3072D → 10D) + **HDBSCAN 聚类** (默认 min_cluster_size=8)
5. **Ward 全档**: 在 N 个细簇质心上做 hierarchical, 切 k=2..N 全档 (`meta_clusters_ward.csv`)
6. **LLM 全档命名**: 顺序遍历 k=2..N, 每档调一次 Claude 命名当前 k 组,
   父档命名注入下一档 context 维持术语一致性 (`meta_ward_labels.json`)
7. 可视化: dendrogram + UMAP 散点 (静态 PNG)
8. 综合报告: 全档命名一览表 + highlight 档详细展开 (`report.md`)
9. **交互可视化** (`interactive.html`): 单文件 HTML (无 CDN 依赖), 给产品/业务方探索:
   ① 客户地图 (UMAP 散点) — Z 选「无」= 2D, 选维度自动 3D 可拖拽旋转;
     悬浮任意点显示业务命名 + 原评论
   ② 客户分群层级树 — 鼠标在树上垂直移动看不同分群粒度对应的命名 + 人数

```bash
python3 lib/pipeline.py --config user_config.yaml
```

成本估算 (N = HDBSCAN 细簇数, 通常 5-50):
- Persona: 数据量 × ~3s (Sonnet medium) / ~15s (Opus xhigh)
- LLM 全档命名: (N-1) 次调用 × ~30s (Sonnet medium) / ~3min (Opus xhigh)
- N=10 时 LLM 命名 ~5 min Sonnet / ~30 min Opus
- N=46 时 LLM 命名 ~22 min Sonnet / ~2.5h Opus (用 `max_k` 限上限省成本)

### 第 3 步: 解读输出

跑完后告诉用户:
- 看 `output/report.md` (全档命名一览 + highlight 档详细展开)
- **`output/interactive.html`** — 在浏览器里打开, 给产品/业务方自助探索 (推荐)
- 用 `output/clusters.parquet` 做下游分析 (每条 persona 含 `ward_meta_2..N` 和 `llm_label_k2..N` 标签)
- `output/meta_ward_labels.json` 是 PPT/业务报告核心交付
- `output/dendrogram.png` / `output/scatter.png` 静态图 (适合截屏插 PPT)

强调:
- **战略级 (k=2/3)** 拿 2-3 名业务总结全市场
- **业务报告 (highlight 档)** 5-15 个画像直接进 PPT
- **长尾 (k=N)** 找 30+ 小众画像
- 跨档下钻: 沿父档命名链, 从粗到细给业务方讲故事

## 关键约束 (从踩坑总结)

1. **不要硬编码产品名 / prompt 关键词** — 全部用 `{product_name}` 占位, config 驱动
2. **embedding 默认 OpenAI 不是 voyage** — voyage 免费层在 >500 条会限流死, OpenAI 30 秒搞定
3. **HDBSCAN min_cluster_size=8 不是默认 15** — 让 20-30 人小众画像有机会
4. **min_length=20 不是 30** — 30 太严会过滤掉 "Have you filed a bug report?" (29 字) 这种诊断追问
5. **全档 LLM 命名是顺序的, 不能并行** — 必须等上一档命名完才能注入下一档 context
6. **数据量 ≥ 500 才推荐**, < 500 直接 LLM tagging
7. **断点续跑**: progress 文件 (`personas_progress.parquet` / `meta_ward_labels_progress.json`) 自动续跑

## 输出物

`output_dir` 下:
- `personas.parquet` — 每条评论 + 生成的 persona
- `embeddings.npy` — embedding 向量
- `clusters.parquet` — `hdbscan_id, ward_meta_2..N, llm_label_k2..N, llm_meta_id, llm_meta_name` 全档列
- `meta_clusters_ward.csv` — 细簇 → 各档 ward_meta_k 数字 mapping
- `meta_ward_labels.json` — **全档 LLM 命名核心交付** (含 rationale + 父档链)
- `meta_llm_raw_k*.txt` — 每档 LLM 原始返回 (debug)
- `dendrogram.png` — Ward 层级树
- `scatter.png` — UMAP 2D 散点 (默认 highlight 档着色)
- `report.md` — 综合人读报告
- **`interactive.html`** — 单文件交互可视化 (Stage 9), 浏览器打开即用, 业务术语零技术门槛

## 配置示例 (按品类)

`config.example.yaml` 内带 3 个 preset:
- `reddit_router_reviews` (本 skill 诞生时的场景)
- `amazon_kitchen_reviews` (Amazon 产品评论)
- `saas_feedback` (产品反馈/客服记录)

用户基于自己品类改 `product_name` 和过滤关键词即可.
