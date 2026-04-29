"""
Merge units.jsonl + analyses.jsonl into a final CSV.
Output is UTF-8 with BOM (utf-8-sig) so Excel renders CJK correctly.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def join_list(v, sep=' | '):
    if not v:
        return ''
    if isinstance(v, list):
        return sep.join(str(x) for x in v if x)
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--units', required=True)
    ap.add_argument('--analyses', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    units_by_id = {}
    with open(args.units, encoding='utf-8') as f:
        for line in f:
            try:
                u = json.loads(line)
            except json.JSONDecodeError:
                continue
            units_by_id[u['unit_id']] = u

    rows = []
    errors = []
    seen_ids = set()
    with open(args.analyses, encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            uid = rec.get('unit_id')
            if not uid or uid in seen_ids:
                continue
            seen_ids.add(uid)
            if 'error' in rec:
                errors.append(rec)
                continue
            unit = units_by_id.get(uid, {})
            a = rec.get('analysis') or {}
            persona = a.get('user_persona') or {}
            rows.append({
                'unit_id': uid,
                'source': rec.get('source', unit.get('source', '')),
                'url': rec.get('url', unit.get('url', '')),
                'author': rec.get('author', unit.get('author', '')),
                'date': rec.get('date', unit.get('date', '')),
                'meta': rec.get('meta', unit.get('meta', '')),
                'relevance': a.get('relevance', ''),
                'language': a.get('language', ''),
                'technical_level': persona.get('technical_level', ''),
                'role': persona.get('role', ''),
                'use_case': persona.get('use_case', ''),
                'household_or_env': persona.get('household_or_env', ''),
                'current_or_prior_gear': persona.get('current_or_prior_gear', ''),
                'isp_or_country': persona.get('isp_or_country', ''),
                'persona_evidence': persona.get('evidence', ''),
                'pain_points': join_list(a.get('pain_points')),
                'praised_aspects': join_list(a.get('praised_aspects')),
                'themes': join_list(a.get('themes')),
                'sentiment_about_product': a.get('sentiment_about_product',
                                                 a.get('sentiment_about_mt6000', '')),
                'purchase_intent': a.get('purchase_intent', ''),
                'summary': a.get('summary', ''),
                'thread_excerpt': (unit.get('thread_text', '') or '')[:1000],
            })

    if not rows:
        print('no rows to write — analyses.jsonl is empty or all errored.')
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f'wrote {len(rows)} rows to {out_path}')
    print(f'errors during analysis: {len(errors)}')
    print('by source:    ', dict(Counter(r['source'] for r in rows)))
    print('by relevance: ', dict(Counter(r['relevance'] for r in rows)))
    print('by sentiment: ', dict(Counter(r['sentiment_about_product'] for r in rows)))

    if errors:
        print('\nfirst 5 errors:')
        for e in errors[:5]:
            print(' ', e.get('unit_id'), '|', str(e.get('error', ''))[:120])


if __name__ == '__main__':
    main()
