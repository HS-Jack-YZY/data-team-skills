# reddit-research-scraping

A Claude Code skill that captures the data team's hard-won methodology for scraping Reddit via Apify — keyword design, community selection, Apify config, funnel diagnosis, go/no-go thresholds, and "when NOT to use Reddit" calls. Pure markdown, no scripts.

This is the **upstream** of `social-reviews-analyzer`: it covers everything from "I want to research users on Reddit" to "I have a clean JSON / CSV ready to analyze." Once the data is collected, hand off to `social-reviews-analyzer` for persona + pain-point extraction.

## Install (for a colleague)

```bash
# 1. Copy this folder into your Claude Code skills dir
cp -r reddit-research-scraping ~/.claude/skills/

# 2. Verify it's loaded next time you start Claude Code:
#    open Claude Code → ask "what skills are available?" → look for
#    "reddit-research-scraping"
```

No Python or other deps — the skill is pure methodology. The model reads it and applies it; you stay in charge of clicking buttons in Apify yourself.

## When the skill triggers

Just describe what you're trying to do in plain language. Examples that should load the skill:

> "我用 apify 抓了 5000 条 reddit 数据想研究用户对智能门锁的吐槽,但只有 200 条有用,哪里出问题了?"

> "我下个月要做扫地机器人的用户研究,主要关心吸力、续航、噪音、宠物毛发,从 reddit 抓数据怎么设计关键词和社区?预算 30 美金。"

> "今天小批跑了 800 条 reddit 数据,有效率才 2%,要不要直接放量到 16 美金?"

> "为什么我用 apify 跑出来的 reddit 数据这么乱?"

> "apify 导出的 csv 行数比预期多了一倍,是不是格式坏了?"

The skill's `description` field also explicitly excludes near-misses — Amazon scraping (use `/scrape-reviews`), already-scraped CSV analysis (use `social-reviews-analyzer`), HTML report generation (use `html-report`), Reddit marketing posting, Apify billing questions, and consumer router questions all do **not** trigger this skill.

## What the skill teaches the model

- **5-step process** with small-batch test as a non-skippable discipline (skip-and-scale = burning $20+ on garbage data, real precedent)
- **Funnel diagnosis framework** — 5 layers (format → topic → dimension → disambiguation → density), each with warning thresholds, plus an explicit tiebreaker rule for when overall rate passes ≥5% but a layer is over its warning line
- **Anti-pattern catalog** — single-token broad nouns without phrase locking, dimension words without category locking, skipping small-batch test, treating competitor names as required keywords
- **Community classification** — 主社区 / 次社区 / 反例 framework with judgment criteria (not a hardcoded subreddit list)
- **Apify config recipe** — JSON not CSV (Reddit markdown tables corrupt CSV), `Limit search to a community` is mandatory, multi-community runs separate, Apify keyword input is **one phrase per line** (not space-joined inline)
- **Failure signals** — explicit "stop and adjust" thresholds while a batch is mid-run
- **When NOT to use Reddit** — per research-topic suitability table (Reddit is great for technical/pain-point discussion, weak for aesthetics, useless for price quantification, etc.)

## What it does NOT do

This skill stops at "you have clean raw data." It deliberately does not:

- Run Apify itself (no SDK integration, no API key handling)
- Write LLM prompts for analyzing the scraped data — that's `social-reviews-analyzer`'s job
- Generate reports — that's `html-report`'s job

The boundary discipline is explicit in the skill's `description` field, so the model won't drift into downstream territory.

## Typical workflow

```
[Research question]
   ↓
reddit-research-scraping skill (this one)
   ├─ design keywords (Apify line-by-line format)
   ├─ pick communities (主/次/反例)
   ├─ run small batch ($3-5, 1000 rows)
   ├─ funnel diagnosis → adjust or scale
   └─ scale up ($15-20, multi-community separate exports)
   ↓
[JSON / CSV files per community]
   ↓
social-reviews-analyzer skill
   ├─ reconstruct conversation trees
   ├─ LLM persona + pain-point extraction
   └─ output structured CSV
   ↓
html-report skill
   └─ produce final PM-facing report
```
