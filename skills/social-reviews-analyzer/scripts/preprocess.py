"""
Reconstruct conversation threads from input CSVs into JSONL analysis units.

Auto-detects each CSV's source type by column signature:
  - Reddit (Apify):  has 'dataType' with post/comment values
  - Discourse forum: has 'topic_id', 'post_number', 'type'
  - Amazon (Apify):  has 'reviewId' and ('_model' or 'productTitle')

Output: one JSON object per line:
  { unit_id, source, url, author, date, meta, thread_text }
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd


# ---------- detection ----------

def detect_source(df: pd.DataFrame) -> str | None:
    cols = set(df.columns)
    if 'dataType' in cols and df['dataType'].astype(str).isin(['post', 'comment']).any():
        return 'reddit'
    if {'topic_id', 'post_number', 'type'}.issubset(cols):
        return 'forum'
    if 'reviewId' in cols and ('_model' in cols or 'productTitle' in cols):
        return 'amazon'
    return None


# ---------- adapters ----------

def from_reddit(df: pd.DataFrame, source_label: str) -> list[dict]:
    units = []
    posts = df[df['dataType'] == 'post']
    comments = df[df['dataType'] == 'comment']

    for _, p in posts.iterrows():
        pid = p.get('parsedId')
        if pd.isna(pid):
            continue
        title = str(p.get('title', '') or '').strip()
        body = str(p.get('body', '') or '').strip()
        sub = str(p.get('subredditName', '') or '').strip()
        author = str(p.get('authorName', '') or '').strip()
        upv = p.get('upVotes', '')

        lines = [f'[POST] r/{sub} | u/{author} | upvotes={upv}']
        if title:
            lines.append(f'TITLE: {title}')
        if body and body.lower() != 'nan':
            lines.append(f'BODY: {body[:1500]}')

        cs = comments[comments['parsedPostId'] == pid].copy()
        nodes = {}
        for _, c in cs.iterrows():
            cid = c.get('id', '')
            parent = c.get('parsedParentId', '')
            nodes[cid] = {
                'parent': parent if parent != pid else None,
                'body': str(c.get('body', '') or '').strip(),
                'author': str(c.get('authorName', '') or '').strip(),
                'upv': c.get('commentUpVotes', ''),
            }

        def depth(cid, seen=None):
            if seen is None:
                seen = set()
            if cid in seen:
                return 0
            seen.add(cid)
            n = nodes.get(cid)
            if not n or not n['parent'] or n['parent'] not in nodes:
                return 0
            return 1 + depth(n['parent'], seen)

        order = sorted(nodes.keys(),
                       key=lambda x: -(nodes[x]['upv'] if isinstance(nodes[x]['upv'], (int, float)) else 0))
        for cid in order[:60]:
            n = nodes[cid]
            d = min(depth(cid), 5)
            indent = '  ' * d
            t = n['body'][:600]
            if not t or t.lower() == 'nan':
                continue
            lines.append(f'{indent}[REPLY d={d}] u/{n["author"]} (+{n["upv"]}): {t}')

        units.append({
            'unit_id': f'{source_label}_{pid}',
            'source': source_label,
            'url': p.get('postUrl', '') or p.get('url', ''),
            'author': author,
            'date': p.get('createdAt', ''),
            'meta': f'subreddit=r/{sub}; upvotes={upv}; n_comments={len(cs)}',
            'thread_text': '\n'.join(lines)[:8000],
        })
    return units


def from_forum(df: pd.DataFrame, source_label: str) -> list[dict]:
    units = []
    for tid, sub in df.groupby('topic_id'):
        topic_row = sub[sub['type'] == 'topic']
        title, url = '', ''
        if not topic_row.empty:
            title = str(topic_row.iloc[0].get('topic_title', '') or '').strip()
            url = str(topic_row.iloc[0].get('url', '') or '').strip()

        full_rows = sub[sub['type'] == 'post_full'].sort_values('post_number')
        post_rows = sub[sub['type'] == 'post'].sort_values('post_number')

        seen_pn = set()
        msgs = []
        op_author, op_date = '', ''
        combined = pd.concat([post_rows, full_rows]).sort_values(['post_number', 'type'])
        for _, r in combined.iterrows():
            pn = r.get('post_number')
            # post_full takes precedence over post (snippet)
            if pn in seen_pn and r['type'] == 'post':
                continue
            seen_pn.add(pn)
            body = str(r.get('body', '') or '').strip()
            if not body or body.lower() == 'nan':
                continue
            user = str(r.get('username', '') or '').strip()
            likes = r.get('like_count', 0)
            tag = '[OP]' if pn == 1.0 else f'[#{int(pn) if pd.notna(pn) else "?"}]'
            msgs.append(f'{tag} u/{user} (+{int(likes) if pd.notna(likes) else 0}): {body[:800]}')
            if pn == 1.0:
                op_author = user
                op_date = str(r.get('created_at', '') or '')
        if not msgs:
            continue

        # Drop low-signal stubs (search-snippet-only with no real content)
        total_chars = sum(len(m) for m in msgs)
        has_full = len(full_rows) > 0
        if not has_full and total_chars < 400:
            continue

        thread = ('TOPIC: ' + title + '\n' if title else '') + '\n'.join(msgs)
        try:
            tid_str = str(int(tid))
        except (TypeError, ValueError):
            tid_str = str(tid)
        units.append({
            'unit_id': f'{source_label}_{tid_str}',
            'source': source_label,
            'url': url,
            'author': op_author,
            'date': op_date,
            'meta': f'topic_id={tid_str}; n_posts={len(seen_pn)}; has_full={has_full}',
            'thread_text': thread[:8000],
        })
    return units


def from_amazon(df: pd.DataFrame, source_label: str, model_filter: str | None) -> list[dict]:
    if model_filter:
        # Match against _model first, fall back to productTitle if _model missing.
        if '_model' in df.columns:
            mask = df['_model'].astype(str).str.contains(model_filter, case=False, na=False, regex=True)
        elif 'productTitle' in df.columns:
            mask = df['productTitle'].astype(str).str.contains(model_filter, case=False, na=False, regex=True)
        else:
            mask = pd.Series([True] * len(df))
        df = df[mask]

    units = []
    for _, r in df.iterrows():
        text = str(r.get('text', '') or '').strip()
        title = str(r.get('title', '') or '').strip()
        if not text and not title:
            continue
        rid = r.get('reviewId', '') or f'idx{_}'
        units.append({
            'unit_id': f'{source_label}_{rid}',
            'source': source_label,
            'url': '',
            'author': str(r.get('userName', '') or ''),
            'date': str(r.get('date', '') or ''),
            'meta': (
                f'rating={r.get("rating", "")}; '
                f'verified={r.get("verified", "")}; '
                f'locale={r.get("locale/country", r.get("domainCode", ""))}'
            ),
            'thread_text': f'TITLE: {title}\nBODY: {text}'[:6000],
        })
    return units


# ---------- main ----------

def parse_overrides(specs: list[str]) -> dict[str, str]:
    out = {}
    for s in specs or []:
        if ':' not in s:
            print(f'WARN: bad --source-override {s!r}, expected path:type', file=sys.stderr)
            continue
        path, kind = s.rsplit(':', 1)
        out[path] = kind
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', help='path to brief.json (used to derive source labels)', default=None)
    ap.add_argument('--inputs', nargs='+', required=True, help='one or more CSV paths')
    ap.add_argument('--out', required=True, help='output JSONL path')
    ap.add_argument('--source-override', action='append', default=[],
                    help='path:type override, e.g. ./mystuff.csv:reddit')
    args = ap.parse_args()

    brief = {}
    if args.brief:
        brief = json.loads(Path(args.brief).read_text(encoding='utf-8'))
    overrides = parse_overrides(args.source_override)

    all_units = []
    for pth in args.inputs:
        df = pd.read_csv(pth)
        kind = overrides.get(pth) or detect_source(df)
        if kind is None:
            print(f'SKIP: could not auto-detect source type for {pth}', file=sys.stderr)
            continue

        # Use file stem to disambiguate sources (e.g. multiple forum CSVs).
        stem = re.sub(r'[^a-zA-Z0-9]+', '_', Path(pth).stem).strip('_').lower()
        label = f'{kind}_{stem}' if kind in ('forum',) else kind

        if kind == 'reddit':
            units = from_reddit(df, label)
        elif kind == 'forum':
            units = from_forum(df, label)
        elif kind == 'amazon':
            units = from_amazon(df, label, brief.get('amazon_model_filter'))
        else:
            print(f'SKIP: unknown override type {kind!r} for {pth}', file=sys.stderr)
            continue
        print(f'{pth}  →  {kind}: {len(units)} units')
        all_units.extend(units)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        for u in all_units:
            f.write(json.dumps(u, ensure_ascii=False) + '\n')

    by_src = {}
    for u in all_units:
        by_src[u['source']] = by_src.get(u['source'], 0) + 1
    print(f'\nTotal units: {len(all_units)}')
    for k, v in by_src.items():
        print(f'  {k}: {v}')
    print(f'Saved to {out_path}')


if __name__ == '__main__':
    main()
