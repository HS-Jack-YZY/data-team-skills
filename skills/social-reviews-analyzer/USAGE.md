# social-reviews-analyzer · 使用与输出指南

> 给数据组同事的"日常使用手册"。SKILL.md 写的是 Claude 触发逻辑，README.md 写的是设计动机，本文写的是**你拿到产品 CSV 之后该怎么操作 + 拿到结果 CSV 后该怎么解读**。

---

## 一、何时用这个 skill

**适合**（直接跑）：
- Apify reddit-scraper 导出的 CSV（含 `dataType` 列）
- Discourse 论坛搜索导出的 CSV（含 `topic_id, post_number, type` 列）—— 比如 openwrt.org、forum.gl-inet.com、discourse.huggingface.co
- Apify Amazon-reviews-scraper 导出的 CSV（含 `reviewId, _model/productTitle` 列）
- 想要的产出是**每行一条**的画像 + 痛点 CSV，可在 Excel/pandas 里二次切片

**不适合**（先想想要不要走这条路）：
- 数据已经聚合好了（NPS 月报、评分均值表）—— skill 要的是原始 thread/review，不是统计结果
- 量级 < 30 条 —— LLM 启动开销摊不平，人肉读更快
- 量级 > 5000 条 —— 当前并行上限 ~10 worker，单跑会很慢，建议分批
- 数据来自 Twitter/X、YouTube、客服工单等 schema 不匹配的源 —— 先在 `scripts/preprocess.py` 加一个 `from_xxx()` adapter

---

## 二、准备（一次性，每台机器一次）

```bash
# 1. 装 pandas
pip3 install --user pandas

# 2. 确认 claude CLI 已登录（skill 用 claude -p 子进程跑 LLM，不用 ANTHROPIC_API_KEY）
claude --version

# 3. 装这个 marketplace（如果还没装）
#    /plugin → marketplace add HS-Jack-YZY/data-team-skills → install data-team-skills
```

确认 skill 已加载：在 Claude Code 里问"现在有哪些 skill 可用？"，应该看到 `data-team-skills:social-reviews-analyzer`。

---

## 三、方式 A：让 Claude Code 自动跑（推荐 ad-hoc 分析）

打开 Claude Code，把 CSV 路径 + 一段产品 brief 贴给它：

```
我要分析 GL.iNet Beryl AX (MT3000) 的用户画像和痛点。
CSV 在：
- /Users/me/scrape/beryl_reddit.csv
- /Users/me/scrape/beryl_forum.csv
- /Users/me/scrape/router_amazon.csv  （混了我家和竞品的 review）

产品别名：MT3000、GL-MT3000、Beryl
品类：便携旅行路由器
竞品：TP-Link AX1500、Anker A55 Hub
帮我用 social-reviews-analyzer 跑一遍。
```

Claude 会：
1. 自动触发 skill（描述里有相应关键词）
2. 帮你把 brief 写成 `brief.json`
3. 后台跑 `preprocess.py` → `analyze.py` → `merge_to_csv.py`
4. 用 Monitor 工具实时报进度（每 50 条一次通知）
5. 完成后给你 CSV 路径 + 统计摘要（按 source / relevance / sentiment 分布）

中途想停就 Ctrl+C，已完成的不会丢；下次同样命令再跑会从断点续。

---

## 四、方式 B：手动跑三条命令（推荐 CI / 自动化 / 想完全控制）

### 1. 写 brief.json

```bash
SKILL=~/.claude/plugins/marketplaces/data-team-skills/skills/social-reviews-analyzer
cp $SKILL/scripts/brief.example.json ./brief.json
$EDITOR brief.json
```

只动 6 个字段：

```json
{
  "product_name": "Beryl AX",
  "product_aliases": ["MT3000", "GL-MT3000", "Beryl"],
  "brand": "GL.iNet",
  "category": "portable travel router",
  "competitors": ["TP-Link AX1500", "Anker A55 Hub"],
  "language_hint": "en"
}
```

### 2. 三步走

```bash
WD=./scratch                       # 中间产物目录
mkdir -p $WD

# Step 1: 重建对话树（约 10 秒）
python3 $SKILL/scripts/preprocess.py \
  --brief brief.json \
  --inputs reddit.csv forum.csv amazon.csv \
  --out $WD/units.jsonl

# Step 2: LLM 分析（几分钟到 1 小时，看数据量）
python3 $SKILL/scripts/analyze.py \
  --brief brief.json \
  --units $WD/units.jsonl \
  --out $WD/analyses.jsonl \
  --workers 6

# Step 3: 合并落盘（UTF-8 BOM, Excel 直接打开不乱码）
python3 $SKILL/scripts/merge_to_csv.py \
  --units $WD/units.jsonl \
  --analyses $WD/analyses.jsonl \
  --out beryl_personas_pain_points.csv
```

`analyze.py` 有几个有用的开关：

| 开关 | 作用 |
|---|---|
| `--limit 10` | 只跑前 10 条单元，快速验证 prompt 没问题 |
| `--workers N` | 并发 LLM 调用数（默认 6，最高建议 10） |
| `--retry-errors` | 把上次 `error` 行重新跑一遍（成功的不动） |
| `--dedupe-only` | 不调 LLM，只去重 `--out` 里同一 unit_id 的多余行 |
| `--model claude-haiku-4-5` | 默认就是 haiku；想用 sonnet 提质量传 `claude-sonnet-4-6` |

---

## 五、brief.json 字段语义

| 字段 | 必填 | 作用 |
|---|---|---|
| `product_name` | ✓ | 产品口语名（"Beryl AX"），写在 prompt 里给 LLM 看 |
| `product_aliases` | ✓ | **最关键**。所有等价名字（型号 SKU、市场名、缩写）。LLM 判定 `relevance` 时实际用的就是这个数组里的字符串 |
| `brand` | ✓ | 品牌名 |
| `category` | ✓ | 品类描述，让 LLM 在 review 里识别"同类比较"的语境 |
| `competitors` | 推荐 | 竞品名清单。LLM 看到这些会标 `relevance: medium`（讨论了同类但不是你的）而不是 `low` |
| `language_hint` | 可选 | 主要语言提示（`en`/`zh`/`de` 等），影响 LLM 输出语种 |

---

## 六、输出 CSV 22 列详解

```
unit_id, source, url, author, date, meta,
relevance, language,
technical_level, role, use_case, household_or_env,
current_or_prior_gear, isp_or_country, persona_evidence,
pain_points, praised_aspects, themes,
sentiment_about_product, purchase_intent,
summary, thread_excerpt
```

### 元数据列（LLM 不动）

| 列 | 含义 | 例子 |
|---|---|---|
| `unit_id` | 唯一 id，回溯用 | `reddit_9s4s9r`、`amazon_R33LJFQT70IW6N` |
| `source` | 来自哪个 scraper 或论坛 | `reddit` / `forum_openwrt` / `forum_gl_inet` / `amazon` |
| `url` | 原帖链接（Reddit / 论坛有；Amazon 一般空） | |
| `author` | 原作者用户名 | `kryoz` |
| `date` | 创建时间，原样透传 | `2026-03-12T...` |
| `meta` | 原始 metadata 字符串 | `subreddit=r/HomeNetworking; upvotes=15; n_comments=8` |
| `thread_excerpt` | 原 thread 文本前 1000 字符，**人工抽查时用** | |

### LLM 抽取的核心列

| 列 | 取值 | 怎么用 |
|---|---|---|
| `relevance` | `high` / `medium` / `low` | **第一道过滤**：`high` = 直接讨论你的产品；`medium` = 同品类比较语境提到；`low` = 噪音 / 不相关。先按这列切片再看其他 |
| `language` | `en` / `zh` / `de` / ... | 国别 / 区域分析 |
| `technical_level` | `beginner` / `intermediate` / `advanced` / `expert` / `unknown` | 用户技术分层。`expert` 用户痛点多是 firmware bug，`beginner` 多是初装失败 |
| `role` | `home_user` / `prosumer` / `homelabber` / `smb_owner` / `sysadmin` / `developer` / `other` / `unknown` | 角色画像。做 GTM 时按这列切目标人群 |
| `use_case` | 自由短语 | "home gaming + 4K streaming"、"travel router for digital nomad"——做场景图谱 |
| `household_or_env` | 自由短语 | "ranch house with 5 cameras + 2 Xboxes"——做使用环境分布 |
| `current_or_prior_gear` | 自由短语 | "Netgear R7000"、"switched from Asus RT-AX86U"——做替换路径分析 |
| `isp_or_country` | 自由短语 | "BT UK fiber"、"Comcast US gigabit"——做地域 / ISP 分布 |
| `persona_evidence` | 一句原文引用 | 让人工抽查时能快速判断 LLM 没乱编 |
| `pain_points` | `\|` 分隔的具体痛点列表 | **核心产物**。"PPPoE drops on firmware 4.5.4 with IPv6 disabled"——具体到固件版本，不是泛泛"WiFi 不好" |
| `praised_aspects` | `\|` 分隔的优点列表 | 营销文案素材；ASIN 五星点提取 |
| `themes` | `\|` 分隔的标签 | "wifi-coverage"、"firmware-bugs"、"vpn"、"mesh"——做云图 / 趋势 |
| `sentiment_about_product` | `positive` / `negative` / `mixed` / `neutral` / `na` | NPS 类口径。`na` = 这条没明确表态（一般 `relevance: low` 同时 `sentiment: na`） |
| `purchase_intent` | `owns` / `considering` / `rejected` / `switched_away` / `na` | **漏斗信号**。`considering` = 漏斗中段，`rejected` = 损失漏斗（一定要看），`switched_away` = 流失（重灾区） |
| `summary` | 1-2 句总结 | 浏览时不用读 thread 原文，扫这一列即可 |

---

## 七、拿到 CSV 怎么切片

### Excel 一分钟搞定

1. 双击打开（UTF-8 BOM 不乱码）
2. 套筛选 → `relevance == "high"` → 只看真正讨论你产品的
3. 数据透视：行=`themes`、值=count → 痛点排行榜
4. 数据透视：行=`role`、列=`sentiment_about_product`、值=count → 不同人群的口碑分布
5. 筛 `purchase_intent == "rejected"` 或 `"switched_away"` → 损失原因清单

### pandas 三个最常用切片

```python
import pandas as pd
df = pd.read_csv('beryl_personas_pain_points.csv', encoding='utf-8-sig')

# 1. 高相关性 + 负面情绪 → 必看清单
hot = df[(df.relevance == 'high') & (df.sentiment_about_product.isin(['negative', 'mixed']))]
print(hot[['unit_id', 'pain_points', 'summary']].head(30))

# 2. 痛点频次（炸开 pipe-separated）
pain_series = df.pain_points.dropna().str.split(' | ').explode().str.strip()
print(pain_series.value_counts().head(20))

# 3. 漏斗各阶段画像
for intent in ['considering', 'rejected', 'switched_away']:
    sub = df[df.purchase_intent == intent]
    print(f'\n=== {intent} ({len(sub)} 条) ===')
    print(sub.role.value_counts())
    print(sub.use_case.value_counts().head(10))
```

### 痛点 → 主题词云

```python
from collections import Counter
themes = Counter()
for t in df.themes.dropna():
    for tag in t.split(' | '):
        themes[tag.strip()] += 1
print(themes.most_common(30))
```

---

## 八、故障兜底

| 现象 | 处理 |
|---|---|
| Step 2 跑到一半挂了 | 同样命令再跑一遍。已成功的 unit_id 跳过，只补未做的 |
| 跑完发现一堆 `error` 行 | `python3 analyze.py ... --retry-errors` 只刷失败的 |
| 怀疑跑了两次产生重复行 | `python3 analyze.py --units ... --out ... --dedupe-only`（不调 LLM） |
| Schema 没自动认出来 | `--source-override path/to/file.csv:reddit`（或 `:forum`、`:amazon`） |
| 想先测 prompt 不烧钱 | `--limit 10 --workers 2`，看输出质量 |
| 输出 CSV 几乎全是 `relevance: low` | brief 写歪了——多半 `product_aliases` 没列全，LLM 认不出你的产品 |
| 中文 CSV 在 Excel 里乱码 | 不该出现，merge 阶段已 BOM。如果用别的工具打开了再保存可能丢 BOM —— 重跑 merge 一次 |

---

## 九、成本与时间预估

模型默认 `claude-haiku-4-5`，每条 unit 约 $0.018–0.025（看 thread 长度）。

| 单元数 | 推荐 workers | 墙钟 | 成本（haiku） |
|---|---|---|---|
| ~100 | 4 | ~3 分钟 | ~$2 |
| ~500 | 6 | ~15 分钟 | ~$10 |
| ~1000 | 8 | ~25 分钟 | ~$20 |
| ~3000 | 10 | ~75 分钟 | ~$60 |

成本走 `claude` 当前登录帐号的额度（订阅或 API）。

> 实测参考：MT6000 这一批 850 个单元，10 worker 并发，22 分钟跑完，$11.89。同一份数据如果用现版本默认行为（不过滤短 forum 帖、不按 model 过滤 Amazon），单元数会涨到 ~3900，成本约 $50–60。

---

## 十、相关文件位置

```
skills/social-reviews-analyzer/
├── SKILL.md               # Claude 触发逻辑 + 完整管道说明（机器读）
├── README.md              # 设计动机、为什么这么做、对外定位（人读）
├── USAGE.md               # 本文：日常使用手册
├── .gitignore
└── scripts/
    ├── preprocess.py      # CSV → units.jsonl（重建对话树）
    ├── analyze.py         # units.jsonl → analyses.jsonl（并行 LLM 调用，幂等）
    ├── merge_to_csv.py    # 合并 → 最终 CSV（UTF-8 BOM）
    └── brief.example.json # brief 模板，复制改用
```

有问题先看 SKILL.md 的 "Failure modes" 段，再看 README 的 "Why reconstruct conversation trees" 段，最后查 git log 看最近的设计变更原因。
