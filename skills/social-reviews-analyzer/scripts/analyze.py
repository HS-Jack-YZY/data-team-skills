"""
Per-unit LLM persona/pain-point extraction. Calls `claude -p` as a subprocess
in parallel, writes one JSON result per line into the output JSONL.

Idempotent: skips unit_ids already present in --out. Resume by re-running.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


SYSTEM_PROMPT = (
    'You are a market-research analyst. You read user-generated content '
    '(reviews, forum threads, reddit threads) and extract structured '
    'persona + pain-point data in strict JSON. Output JSON only — no prose, '
    'no markdown fences.'
)

USER_PROMPT_TEMPLATE = """You are analyzing user-generated content related to the product below. Use the FULL conversation context (post + replies) to ground your judgment, but focus persona extraction on the original poster (or reviewer) unless multiple distinct users are clearly identifiable.

PRODUCT BRIEF:
{brief_block}

Return strictly one JSON object with this schema (use empty string / empty array if data is not present — do not invent):

{{
  "relevance": "high" | "medium" | "low",   // does this thread directly discuss the product (or a clear alias from the brief)?  high = directly mentioned/used; medium = related category, weak link; low = unrelated noise
  "language": "en" | "zh" | "de" | "...",
  "user_persona": {{
    "technical_level": "beginner" | "intermediate" | "advanced" | "expert" | "unknown",
    "role": "home_user" | "prosumer" | "homelabber" | "smb_owner" | "sysadmin" | "developer" | "other" | "unknown",
    "use_case": "free-form short phrase, e.g. 'home gaming + 4K streaming', 'travel router for digital nomad'",
    "household_or_env": "free-form, e.g. 'large 2-story house, 30 devices', 'apartment, 5 devices'",
    "current_or_prior_gear": "any product/brand they own or compare against",
    "isp_or_country": "if mentioned (e.g., 'BT UK fiber', 'Comcast US gigabit')",
    "evidence": "1 short quote or paraphrase from the text supporting the persona"
  }},
  "pain_points": [
    // each item = a SPECIFIC user-reported issue, frustration, or unmet need.
    // Be specific (e.g. 'PPPoE drops on firmware 4.5.4 with IPv6 disabled'),
    // not generic ('bad wifi'). Include those raised by repliers too.
    "..."
  ],
  "praised_aspects": ["aspects users explicitly liked"],
  "themes": ["short tags, e.g. 'wifi-coverage', 'vpn', 'firmware-bugs', 'gaming', 'mesh', 'vlan', 'ipv6'"],
  "sentiment_about_product": "positive" | "negative" | "mixed" | "neutral" | "na",
  "purchase_intent": "owns" | "considering" | "rejected" | "switched_away" | "na",
  "summary": "1-2 sentences capturing the gist."
}}

CONTENT (source={source}, meta={meta}):
---
{thread_text}
---
Output the JSON object only.
"""


# ---------- helpers ----------

def extract_json(text: str):
    """Parse first balanced { ... } JSON object from text (tolerates ```json fences)."""
    if not text:
        return None
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def render_brief(brief: dict) -> str:
    if not brief:
        return '(no brief provided — judge relevance from content alone)'
    parts = []
    for k in ('product_name', 'brand', 'category'):
        if brief.get(k):
            parts.append(f'- {k}: {brief[k]}')
    if brief.get('product_aliases'):
        parts.append(f'- product_aliases (treat these as same product): {", ".join(brief["product_aliases"])}')
    if brief.get('competitors'):
        parts.append(f'- competitors (mentioned for comparison context): {", ".join(brief["competitors"])}')
    return '\n'.join(parts) or '(brief is empty)'


def analyze_unit(unit: dict, brief_block: str, model: str, workdir: str, timeout: int = 120) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(
        brief_block=brief_block,
        source=unit['source'],
        meta=unit.get('meta', ''),
        thread_text=unit['thread_text'],
    )
    try:
        res = subprocess.run(
            [
                'claude', '-p',
                '--output-format', 'json',
                '--model', model,
                '--append-system-prompt', SYSTEM_PROMPT,
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        if res.returncode != 0:
            return {'unit_id': unit['unit_id'],
                    'error': f'returncode={res.returncode}: {(res.stderr or "").strip()[:300]}'}
        outer = json.loads(res.stdout)
        if outer.get('is_error'):
            return {'unit_id': unit['unit_id'], 'error': str(outer.get('result', ''))[:300]}
        parsed = extract_json(outer.get('result', ''))
        if parsed is None:
            return {'unit_id': unit['unit_id'],
                    'error': f'json_parse_failed: {str(outer.get("result", ""))[:200]}'}
        return {
            'unit_id': unit['unit_id'],
            'source': unit['source'],
            'url': unit.get('url', ''),
            'author': unit.get('author', ''),
            'date': unit.get('date', ''),
            'meta': unit.get('meta', ''),
            'cost_usd': outer.get('total_cost_usd', 0),
            'analysis': parsed,
        }
    except subprocess.TimeoutExpired:
        return {'unit_id': unit['unit_id'], 'error': 'timeout'}
    except Exception as e:
        return {'unit_id': unit['unit_id'], 'error': f'{type(e).__name__}: {str(e)[:200]}'}


def dedupe_jsonl(path: Path):
    """Keep best record per unit_id (success preferred over error). Rewrites in place."""
    if not path.exists():
        return 0
    by_id = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            uid = r.get('unit_id')
            if uid is None:
                continue
            cur = by_id.get(uid)
            if cur is None:
                by_id[uid] = r
            elif 'error' in cur and 'error' not in r:
                by_id[uid] = r
    with open(path, 'w', encoding='utf-8') as f:
        for r in by_id.values():
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return len(by_id)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', help='path to brief.json', default=None)
    ap.add_argument('--units', required=True, help='units.jsonl from preprocess.py')
    ap.add_argument('--out', required=True, help='output analyses.jsonl (appended; idempotent)')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--model', default='claude-haiku-4-5')
    ap.add_argument('--limit', type=int, default=None,
                    help='process only first N pending units (smoke test)')
    ap.add_argument('--retry-errors', action='store_true',
                    help='also retry units whose previous result was an error')
    ap.add_argument('--dedupe-only', action='store_true',
                    help='only deduplicate --out by unit_id (no LLM calls)')
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dedupe_only:
        n = dedupe_jsonl(out_path)
        print(f'deduped: {n} unique unit_ids in {out_path}')
        return

    brief = {}
    if args.brief:
        brief = json.loads(Path(args.brief).read_text(encoding='utf-8'))
    brief_block = render_brief(brief)

    units = [json.loads(l) for l in open(args.units, encoding='utf-8')]

    done_ok, done_err = set(), set()
    if out_path.exists():
        with open(out_path, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                uid = r.get('unit_id')
                if not uid:
                    continue
                if 'error' in r:
                    done_err.add(uid)
                else:
                    done_ok.add(uid)

    skip = done_ok if args.retry_errors else (done_ok | done_err)
    pending = [u for u in units if u['unit_id'] not in skip]
    if args.limit:
        pending = pending[:args.limit]
    print(f'Total units: {len(units)} | already ok: {len(done_ok)} | '
          f'prior errors: {len(done_err)} | this run: {len(pending)} | workers: {args.workers}')

    workdir = '/tmp/sra_workdir'
    os.makedirs(workdir, exist_ok=True)

    # If we are retrying errors, drop their old rows so they get rewritten.
    if args.retry_errors and done_err:
        keep = []
        with open(out_path, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if 'error' not in r:
                    keep.append(line.rstrip('\n'))
        with open(out_path, 'w', encoding='utf-8') as f:
            for line in keep:
                f.write(line + '\n')

    out_f = open(out_path, 'a', encoding='utf-8')
    n_done, n_err, total_cost, t0 = 0, 0, 0.0, time.time()
    try:
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(analyze_unit, u, brief_block, args.model, workdir): u for u in pending}
            for fut in cf.as_completed(futs):
                rec = fut.result()
                if 'error' in rec:
                    n_err += 1
                else:
                    total_cost += rec.get('cost_usd', 0)
                out_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                out_f.flush()
                n_done += 1
                if n_done % 5 == 0 or n_done == len(pending):
                    elapsed = time.time() - t0
                    rate = n_done / max(elapsed, 1)
                    eta = (len(pending) - n_done) / max(rate, 1e-6)
                    print(f'[{n_done}/{len(pending)}] errors={n_err} '
                          f'cost=${total_cost:.2f} rate={rate:.2f}/s eta={eta:.0f}s',
                          flush=True)
    finally:
        out_f.close()


if __name__ == '__main__':
    main()
