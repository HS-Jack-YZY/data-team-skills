# customer-persona-clustering

完整的客户画像聚类 skill — 通用产品适用，**Ward 全档 + LLM 逐档命名 + 父档术语注入**。

## 一句话

把任意产品（路由器 / 厨具 / SaaS）的用户评论 → 全档（k=2..N）带业务命名的客户画像树，业务方按需选 k 切刀。

## 文件结构

```
~/.claude/skills/customer-persona-clustering/
├── SKILL.md                # Claude Code 加载的入口 (元数据 + 触发说明)
├── README.md               # 本文档
├── config.example.yaml     # 配置模板, 用户 cp 一份改
├── lib/
│   ├── pipeline.py         # 一站式 orchestrator (9 个 stage)
│   └── interactive.py      # Stage 9: 自包含交互可视化 HTML 生成器
└── prompts/
    ├── persona.md          # Stage 2: 个体 persona 生成 prompt
    └── meta_merge.md       # Stage 6: LLM 概念合并 prompt
```

## 9 个流水线阶段

| Stage | 名字 | 输入 | 输出 | 时间 |
|---|---|---|---|---|
| 1 | load_filter | CSV | filtered.parquet | 秒 |
| 2 | persona | filtered.parquet | personas.parquet | **大头** (1000 条 ~30 min Max + workers=2) |
| 3 | embed | personas.parquet | embeddings.npy | 30 秒 (OpenAI) |
| 4 | cluster | embeddings.npy | clusters.parquet | 5 min (UMAP 主) |
| 5 | meta_ward | clusters.parquet | meta_clusters_ward.csv (全档 k=2..N 列) | 秒 |
| 6 | meta_llm | clusters.parquet | **meta_ward_labels.json** (全档 LLM 命名 + 父档链) | (N-1) × ~30s Sonnet / ~3min Opus |
| 7 | visualize | clusters.parquet | dendrogram.png + scatter.png | 秒 |
| 8 | report | clusters.parquet | report.md (全档汇总 + highlight 详细) | 秒 |
| **9** | **interactive** | clusters/labels/linkage/umap_nd | **interactive.html** (单文件交互可视化) | 秒 |

## 快速开始

```bash
# 1. cp 一份配置到你的项目目录
cp ~/.claude/skills/customer-persona-clustering/config.example.yaml my_project_config.yaml

# 2. 改配置 — 必改字段:
#    product_name, product_category, input_csv, text_column
#    optional_columns (如果是 Reddit/论坛, 配 parent_id/post_id 解锁上下文树)

# 3. 装依赖 (一次性)
pip install pandas numpy scipy scikit-learn umap-learn hdbscan matplotlib pyyaml \
            openai voyageai google-genai claude-agent-sdk

# 4. 设 API key (按你 config 选的 provider)
export OPENAI_API_KEY=sk-proj-...      # embedding (推荐)
# 或 export VOYAGE_API_KEY=...
# 或 export GOOGLE_API_KEY=...

# 5. 跑全套
python3 ~/.claude/skills/customer-persona-clustering/lib/pipeline.py --config my_project_config.yaml

# 或用预设 (config 内带 reddit_router_reviews / amazon_kitchen_reviews / saas_feedback)
python3 ~/.claude/skills/customer-persona-clustering/lib/pipeline.py \
    --config my_project_config.yaml --preset reddit_router_reviews

# 跑单个或几个阶段 (debug 用)
python3 .../pipeline.py --config x.yaml --stages embed,cluster,meta_ward
```

## 输出物

`{output_dir}` 下：

| 文件 | 内容 | 用途 |
|---|---|---|
| **`interactive.html`** | 单文件交互可视化（散点 + 层级树, 鼠标悬浮看详情, 业务术语零门槛） | **产品 / 业务方自助探索** |
| `report.md` | 综合人读报告，全档命名一览 + highlight 详细 | 数据组第一个看的 |
| `clusters.parquet` | 每条评论 + persona + 全档 ward_meta_k / llm_label_k 标签 | 下游分析 |
| `meta_ward_labels.json` | **全档 LLM 命名** + rationale + 父档链 | **PPT / 业务报告核心** |
| `meta_clusters_ward.csv` | 细簇 → 各档 ward_meta_k 数字 mapping | 选任意 k 切刀 |
| `meta_llm_raw_k*.txt` | 每档 LLM 原始返回 | debug 用 |
| `dendrogram.png` | Ward 层级树 | 截图插 PPT |
| `scatter.png` | UMAP 2D 散点（默认 highlight 档着色） | 截图插 PPT |

## 全档画像粒度（业务用法）

| 粒度 | 来源 | 适用 |
|---|---|---|
| **细 (k=N)** | `meta_ward_labels.json` 的 `k=N` 档 | 长尾营销 / 找 niche |
| **业务报告 (highlight 档)** | `meta_ward_labels.json` 的 highlight k 档 (默认 5/10/15/20) | **业务报告 / PPT 主体** |
| **战略级 (k=2/3)** | `meta_ward_labels.json` 的 `k=2`/`k=3` 档 | 老板视图 / 全市场 2-3 名总结 |

跨档下钻: 沿 `parents.parent_name` 字段从粗档到细档串成命名链, 给业务方讲 "家用用户 → 家用-易用性派 → 家用-易用-说明书优先" 的故事.

## 默认配置（基于踩坑总结）

| 参数 | 默认值 | 为什么这么定 |
|---|---|---|
| embedding provider | OpenAI | voyage 免费层 >500 条会限流死, OpenAI 30 秒搞定 |
| embedding model | text-embedding-3-large (3072D) | -small (1536D) 会吞掉小众画像 |
| HDBSCAN min_cluster_size | **8** | 默认 15 太保守, 8 让 20-30 人小众有机会 |
| min_length filter | **20** | 30 太严会过滤 "Have you filed a bug report?" 这种 29 字诊断追问 |
| Ward levels (highlight) | [5, 10, 15, 20] | report 里详细展开的几档, 不影响实际全档命名范围 |
| LLM max_k | null (= 全档 N) | 全覆盖, k=2..N 都标. 设数字限上限省成本 |
| LLM effort | high | xhigh 慢但只给个位数提升 |

## Ward 全档 + LLM 逐档命名

工作方式:
1. **Ward 算全档**: 在 N 个 HDBSCAN 细簇质心上做 hierarchical, 切出 k=2..N 共 N-1 档
2. **LLM 逐档命名**: 顺序遍历 k=2 → k=3 → ... → k=N, 每档调一次 Claude 命名
3. **父档术语注入**: k=5 调用时把 k=4 的命名作为 context 传入, LLM 子组命名承接父名风格
4. **跨档下钻**: `parents.parent_name` 字段记录每个 ward 组从哪个父 split 出来, 业务方拿到完整命名链

输出 `meta_ward_labels.json` 结构:
```json
{
  "n_细簇": 12, "k_max": 12,
  "k_labeled": [2, 3, ..., 12],
  "levels_highlight": [3, 5, 8],
  "by_k": {
    "k=3": {"labels": [{"id": 1, "name": "...", "size": 80, "rationale": "...", "hdbscan_members": [...]}]},
    "k=5": {"labels": [...], "parents": {"1": {"parent_id": 1, "parent_name": "..."}}}
  }
}
```

## 何时不用这个 skill

- **数据量 < 100 条** → 样本太少，聚类不可靠，直接 LLM tagging 即可
- **只想看话题分布** → 用 BERTopic 或 c-TF-IDF 类工具，不需要画像生成
- **要做实时分类** → 把训练好的 cluster centroid 存下来用 nearest neighbor，不用 skill

## 已知坑（写在 SKILL.md 也再说一遍）

1. **不要硬编码产品名**：全部走 config，prompt 里 `{product_name}` 占位
2. **embedding 默认 OpenAI 不是 voyage**：Voyage 免费层踩坑教训
3. **HDBSCAN min_cluster_size=8 不是默认 15**：让小众画像有机会
4. **min_length=20 不是 30**：30 太严，会过滤掉 "Have you filed a bug report?" (29 字) 这种诊断追问
5. **全档 LLM 命名顺序执行**：父档命名要注入下一档 context，不能并行
6. **断点续跑**：`personas_progress.parquet` / `meta_ward_labels_progress.json` 自动续
7. **数据量 ≥ 500 才推荐**

## 版本

- v1.0 (2026-05-04): 首版，含 8 stage + 双合并方案 + 3 个产品预设
- v2.0 (2026-05-04): 重构为 **Ward 全档 + LLM 逐档命名 + 父档术语注入**。`meta_clusters_llm.json` → `meta_ward_labels.json`，`target_k` → `max_k`，删 ARI 一致性检查（同一棵树无意义）
- v2.1 (2026-05-04): 新增 **Stage 9 `interactive`** — 自包含交互可视化 HTML（散点 + 层级树, 业务术语 / 鼠标悬浮看原评论 / 2D-3D 切换 / 拖拽旋转），给产品 / 业务方零门槛自助探索；修复 `/review-pr` 揭示的全部 8 个 Critical bug

## 关联 skill

- `social-reviews-analyzer` (旧版): 仅 LLM tagging，无聚类。本 skill 是它的进阶版。
- `data-team-skills:html-report`: 把本 skill 的 report.md 转成漂亮 HTML 报告
- `data-team-skills:delivery-message`: 把分析结果包装成数据组对外发布消息
