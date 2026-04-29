# social-reviews-analyzer

A Claude Code skill that turns scraped Reddit threads, Discourse forum exports, and Amazon reviews into one merged CSV of **user personas + pain points** — using an LLM for actual semantic analysis (not keyword matching), with full conversation-tree context preserved.

## Install (for a colleague)

```bash
# 1. Copy this folder into your Claude Code skills dir
cp -r social-reviews-analyzer ~/.claude/skills/

# 2. Make sure pandas is available (the only Python dep)
pip3 install --user pandas

# 3. Verify the skill is registered next time you start Claude Code:
#    open Claude Code → ask "what skills are available?" → look for
#    "social-reviews-analyzer"
```

That's it. The pipeline calls `claude -p` as a subprocess for each thread, so as long as `claude --version` works in your terminal, the skill works.

## What you give it

- **One or more CSV files** of scraped content. Source type is auto-detected:
  - Reddit (Apify scraper) — has `dataType` column
  - Discourse forum scrape — has `topic_id` / `post_number` / `type` columns
  - Amazon (Apify scraper) — has `reviewId` and `_model` / `productTitle`
- **A `brief.json`** describing the product. See `scripts/brief.example.json`. The brief is what makes the analysis specific to your product instead of generic.

## What you get back

One CSV (UTF-8 with BOM, opens cleanly in Excel) where each row is one analysis unit — a Reddit thread, a forum topic, or an Amazon review. Columns include persona (technical level, role, use case, gear, ISP), pain points, praised aspects, themes, sentiment about your product, purchase intent, and a one-line summary.

## How to invoke it from Claude Code

Just ask in plain language. Examples that should trigger the skill:

> "I scraped some Reddit threads and Amazon reviews about our router — can you analyze users' pain points? Files are at `~/Desktop/router_data/`."

> "Pull out user portraits and pain points from these forum CSVs."

> "Run social-reviews-analyzer on `data/reddit.csv data/amazon.csv`. Product is the X-7000 from Acme."

Claude will ask for the brief if you didn't provide one, then run preprocess → analyze → merge. For a few hundred units it's a few minutes; for a thousand it's about 25 minutes and ~$15–25 of API credit.

## Manual invocation (if you want to run it without Claude)

```bash
SKILL=~/.claude/skills/social-reviews-analyzer
WD=/path/to/scratch
mkdir -p $WD

# write your brief.json (copy from scripts/brief.example.json)
$EDITOR $WD/brief.json

python3 $SKILL/scripts/preprocess.py \
  --brief $WD/brief.json \
  --inputs reddit.csv forum.csv amazon.csv \
  --out $WD/units.jsonl

python3 $SKILL/scripts/analyze.py \
  --brief $WD/brief.json \
  --units $WD/units.jsonl \
  --out $WD/analyses.jsonl \
  --workers 6

python3 $SKILL/scripts/merge_to_csv.py \
  --units $WD/units.jsonl \
  --analyses $WD/analyses.jsonl \
  --out my_personas_pain_points.csv
```

The pipeline is fully resumable — if `analyze.py` is interrupted, just re-run the same command and it picks up where it left off. To retry only the failed units after a crash, add `--retry-errors`.

## Why "reconstruct conversation trees" matters

A comment like *"yeah I had the same problem"* is useless on its own — you need to see what *the same problem* refers to. The preprocessor stitches each Reddit comment back to its parent and post via `parsedParentId`, indents replies by depth, and sorts by upvotes so the LLM sees the most useful 60 comments per thread in context. For Discourse forums it groups by `topic_id` and prefers `post_full` rows over truncated search snippets, ordering by `post_number`. This is the single biggest lever on output quality.

## Cost & runtime

| Units | Workers | Wall time | Cost (haiku-4-5) |
| ----- | ------- | --------- | ---------------- |
| ~100  | 4       | ~3 min    | ~$2              |
| ~500  | 6       | ~15 min   | ~$10             |
| ~1000 | 8       | ~25 min   | ~$20             |

Cost is whatever your `claude` CLI is logged into.

## Files

```
social-reviews-analyzer/
├── SKILL.md                  # what the skill does, how to trigger, full pipeline doc
├── README.md                 # this file (for the human)
└── scripts/
    ├── preprocess.py         # CSVs → units.jsonl  (rebuilds conversation trees)
    ├── analyze.py            # units.jsonl → analyses.jsonl  (LLM extraction, parallel, idempotent)
    ├── merge_to_csv.py       # merge → final CSV (UTF-8 BOM)
    └── brief.example.json    # template brief, copy and edit
```
