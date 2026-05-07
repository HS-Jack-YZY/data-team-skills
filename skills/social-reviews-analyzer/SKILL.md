---
name: social-reviews-analyzer
description: Turn raw social-media + e-commerce review CSVs (Reddit, Discourse forums, Amazon) into a single merged CSV of user personas + pain points using LLM semantic analysis. Use this skill whenever the user wants to extract user portraits, pain points, sentiment, or themes from scraped Reddit threads, forum discussions, or Amazon reviews about a product or competitor — even if they only mention "analyze these reviews", "extract pain points", "user research from social data", or just hand over CSVs that look like they came from Apify/Discourse scrapers. Reconstructs conversation trees so the LLM has full thread context, not isolated comments.
---

# Social-Reviews-Analyzer

Turn scraped social media + review CSVs into a clean persona / pain-point CSV that a PM, marketer, or researcher can act on.

## When to use this

Use this skill when **all** of the following are true:

1. The user has **one or more CSV files** of user-generated content — Reddit posts/comments, Discourse-style forum threads (e.g. openwrt.org, forum.gl-inet.com, discuss.huggingface.co), or Amazon product reviews (typically scraped via Apify).
2. They want a **structured analysis** of users — personas, pain points, sentiment, themes — not just a summary.
3. They want **per-thread / per-review** rows in the output, not a single executive summary.

If the user only has one product review and wants a one-off summary, you don't need this skill — just answer in chat.

If the user wants strategic synthesis across the whole dataset (top 5 themes, market positioning), run this skill first to produce the per-row CSV, then summarize from that.

## What it produces

A single CSV at the path the user specifies (default: alongside their inputs), encoded **UTF-8 with BOM** so it opens cleanly in Excel without garbling Chinese/CJK characters. Each row is one analysis unit (one Reddit thread, one forum topic, or one Amazon review) with these columns:

```
unit_id, source, url, author, date, meta,
relevance, language,
technical_level, role, use_case, household_or_env,
current_or_prior_gear, isp_or_country, persona_evidence,
pain_points, praised_aspects, themes,
sentiment_about_product, purchase_intent,
summary, thread_excerpt
```

`pain_points`, `praised_aspects`, `themes` are pipe-joined (`a | b | c`).

## Pipeline

Three scripts, run in order. They live in `scripts/` next to this SKILL.md.

```
1. scripts/preprocess.py   — input CSVs    →  units.jsonl  (one analysis unit per line)
2. scripts/analyze.py      — units.jsonl   →  analyses.jsonl  (LLM-extracted JSON per unit)
3. scripts/merge_to_csv.py — both files    →  final CSV (UTF-8 BOM)
```

Each step is **idempotent** — `analyze.py` skips units already in `analyses.jsonl`, so a crash or rate-limit halt does not waste prior work. Resume by re-running the same command.

## How to invoke

### Step 1 — gather the brief from the user

Ask (or infer from conversation) and record into a `brief.json`:

```json
{
  "product_name": "Flint 2",
  "product_aliases": ["MT6000", "GL-MT6000", "Flint2"],
  "brand": "GL.iNet",
  "category": "WiFi 6 router",
  "competitors": ["Asus RT-BE88U", "TP-Link Archer BE700"],
  "language_hint": "en"
}
```

- `product_aliases` is the most important field — these strings drive how the LLM judges per-unit relevance to your focal product.
- `competitors` is optional context handed to the LLM so it can recognize comparison framing.
- **Amazon CSVs are not filtered by model.** If your Amazon CSV mixes your product with competitors (typical of "scrape my product + 5 competitors" workflows), all rows are kept — competitor reviews carry valuable category-level persona / pain-point signal, and the LLM tags relevance per unit so you can filter on the output CSV. If you only want your own product's reviews, pre-filter the CSV before running.

### Step 2 — locate inputs

Inputs are simply a list of CSV paths. Source type is **auto-detected by columns**:

| Source            | Detection rule                                             |
| ----------------- | ---------------------------------------------------------- |
| Reddit (Apify)    | has `dataType` column with values `post`/`comment`         |
| Discourse forum   | has `topic_id`, `post_number`, and `type` columns          |
| Amazon (Apify)    | has `reviewId` and `_model` (or `productTitle`) columns    |

If a CSV does not match any rule, the preprocessor will print a warning and skip it. The user can then either rename columns or pass `--source-override <path>:<type>`.

### Step 3 — run the pipeline

**Default paths** (when running inside a GL.iNet ticket workflow — the parent directory contains a `<ticket_id>_<slug>/` folder created by `ticket-aligner`):

```bash
TICKET_DIR=$(ls -d <编号>_*/ 2>/dev/null | head -n 1)
WORKDIR="$TICKET_DIR/data/scratch"                             # intermediate jsonl + logs (gitignored)
FINAL_CSV="$TICKET_DIR/data/analyzed/${PRODUCT}_reviews.csv"   # final merged sample (analyzed deliverable)
mkdir -p "$WORKDIR" "$(dirname "$FINAL_CSV")"
```

**Fallback** (no ticket workflow — ad-hoc analysis, e.g. external CSVs you want to triage): use any directory of your choice for `WORKDIR` and any path for the final CSV.

**`data/` 子目录约定**（与 ticket-plan 三层目录约定对齐）：

| 子目录            | 角色                                          | git 跟踪 |
| ----------------- | --------------------------------------------- | -------- |
| `data/raw/`       | 原始抓取（本 skill 不写这一层）               | ✅       |
| `data/analyzed/`  | 分析结果（merged CSV 落这里 ← 本 skill 输出） | ✅       |
| `data/scratch/`   | 中间产物（units / analyses jsonl + 日志）     | ❌       |

`scratch/` 是 `raw/` `analyzed/` 之外的**第三个并列子目录**，不是 `analyzed/` 的子目录、也不是 `raw/` 的子目录——专门承载流水线中间态，不进 git、不参与对外交付。

**Recommended `.gitignore` entry** for ticket workflow:

```
# in <编号>_<slug>/.gitignore (or repo root if you don't want per-ticket .gitignore)
data/scratch/
```

`scratch/` holds `units.jsonl` (~MB), `analyses.jsonl` (~MB), and per-run logs. None of these are deliverables — they are intermediate artifacts that can be regenerated by re-running the pipeline. Keeping them out of git keeps the ticket folder lean.

**Pipeline invocation**:

```bash
python3 ~/.claude/skills/social-reviews-analyzer/scripts/preprocess.py \
  --brief brief.json \
  --inputs reddit.csv forum1.csv amazon.csv \
  --out "$WORKDIR/units.jsonl"

python3 ~/.claude/skills/social-reviews-analyzer/scripts/analyze.py \
  --brief brief.json \
  --units "$WORKDIR/units.jsonl" \
  --out "$WORKDIR/analyses.jsonl" \
  --workers 6 \
  --model claude-haiku-4-5

python3 ~/.claude/skills/social-reviews-analyzer/scripts/merge_to_csv.py \
  --units "$WORKDIR/units.jsonl" \
  --analyses "$WORKDIR/analyses.jsonl" \
  --out "$FINAL_CSV"
```

> If the merged CSV exceeds ~50 MB, consider keeping only a head/tail sample (≤ 1000 rows) in `data/analyzed/` and putting the full CSV on shared storage — `data/analyzed/` is meant for shareable samples that can travel with the ticket folder, not raw multi-GB dumps.

### Step 4 — monitor & report

`analyze.py` prints `[N/total] errors=K cost=$X` every 5 units. For datasets of a few hundred to a few thousand units, run it as a background task and use the Monitor tool (or `tail -f`) to surface progress to the user. A typical 800-unit run with `--workers 6` against `claude-haiku-4-5` finishes in ~25 minutes and costs roughly $15–25 of API credit (cost reflects whatever account `claude` is logged into).

After the run, sanity-check the output by reading the first 20 rows of the CSV — confirm personas vary, pain points are concrete (not generic), and the source breakdown matches what the user expected.

## Cost & runtime ballpark

| Units | Workers | Wall time | Cost (haiku-4-5) |
| ----- | ------- | --------- | ---------------- |
| ~100  | 4       | ~3 min    | ~$2              |
| ~500  | 6       | ~15 min   | ~$10             |
| ~1000 | 8       | ~25 min   | ~$20             |

These are approximate — short Reddit/Amazon units cost less, long forum threads with many replies cost more.

## Failure modes & how to handle them

- **Empty stderr `returncode=1`**: usually transient (rate limits or transport hiccup). Re-run `analyze.py` — successful units are remembered, only the failed ones retry. If errors persist, drop `--workers` to 3.
- **Concurrent runs on the same `analyses.jsonl`**: do not start a second `analyze.py` against the same out-file. They will both append and produce duplicates. If duplicates already happened, run `python3 -m json.tool` to dedupe by `unit_id` before merging (the `analyze.py` script can also be invoked with `--dedupe-only` to clean an output file in place).
- **CSV not auto-detected**: pass `--source-override path/to/file.csv:reddit` (or `:forum`, `:amazon`).
- **Analysis quality looks shallow** for low-content threads: this is expected. Short forum hits where the product is only mentioned in passing get a `relevance: low` (or `medium`) tag from the LLM. The preprocessor deliberately does **not** drop them — casual single-mentions are valuable share-of-voice signal (which competitors users mention you alongside, what use cases they bring up, mention frequency). Filter the final CSV to `relevance != low` if you only want deep / actionable rows; keep them all if you want breadth analysis.

## Why reconstruct conversation trees

Isolated comments are nearly useless for persona analysis — "Yeah I switched too" tells you nothing without the parent. The preprocessor:

- For **Reddit**: links each comment to its post via `parsedPostId` and recursively to its parent via `parsedParentId`, then emits the post + top-N comments (sorted by upvotes, indented by reply depth) as one prompt.
- For **Discourse forums**: groups all rows of the same `topic_id`, prefers `post_full` rows over truncated `post` snippets, and orders by `post_number` so the LLM sees the OP question first then the discussion. Even single-snippet hits (the topic was matched by the search but no full body was scraped) are kept — they still carry useful "this user mentioned the product alongside X" signal. The LLM tags relevance per unit; you decide downstream whether to filter.
- For **Amazon**: each review is already self-contained, so the unit is `title + body + rating + verified`.

This is the single biggest quality lever — without it the LLM hallucinates personas from fragments.

## Reference: brief.json schema

See `scripts/brief.example.json` for a fully-commented example a user can copy and edit.
