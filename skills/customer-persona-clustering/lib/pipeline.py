"""
customer-persona-clustering — 完整流水线 orchestrator

8 个阶段:
  1. load_filter      加载 CSV + 噪声过滤
  2. persona_generate 用 Claude 生成 persona (上下文树重建)
  3. embed            embedding (OpenAI / Voyage / Gemini)
  4. cluster          UMAP + HDBSCAN
  5. meta_ward        方案 A: Ward 质心层级合并 → 5/10/15/20 多档
  6. meta_llm         方案 C: LLM 概念合并 + 业务命名
  7. visualize        dendrogram + UMAP 2D 散点
  8. report           综合人读报告 (含 ARI 一致性)

用法:
  python3 pipeline.py --config user_config.yaml             # 跑全套
  python3 pipeline.py --config x.yaml --stages embed,cluster  # 跑指定阶段
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


SKILL_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = SKILL_ROOT / "prompts"


# ============================================================================
# Config & utilities
# ============================================================================
def load_config(path: Path, preset: str | None = None) -> dict:
    cfg = yaml.safe_load(path.read_text())
    if preset and preset in cfg.get("presets", {}):
        for k, v in cfg["presets"][preset].items():
            cfg[k] = v
    cfg.pop("presets", None)
    return cfg


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_api_key(env_name: str) -> str:
    key = os.environ.get(env_name)
    if not key:
        sys.exit(f"✗ 环境变量 {env_name} 未设置")
    return key


# ============================================================================
# Stage 1: load_filter
# ============================================================================
def stage_load_filter(cfg: dict, out_dir: Path) -> Path:
    print("\n=== Stage 1: 加载 + 噪声过滤 ===")
    df = pd.read_csv(cfg["input_csv"])
    text_col = cfg["text_column"]
    print(f"  原始: {len(df)} 行")

    df[text_col] = df[text_col].fillna("").astype(str)

    for f in cfg.get("noise_filters", []):
        before = len(df)
        if f["type"] == "min_length":
            df = df[df[text_col].str.len() >= f["chars"]]
        elif f["type"] == "contains":
            mask = pd.Series([True] * len(df), index=df.index)
            for pat in f["patterns"]:
                mask &= ~df[text_col].str.contains(pat, na=False, regex=False)
            df = df[mask]
        elif f["type"] == "regex":
            mask = pd.Series([True] * len(df), index=df.index)
            for pat in f["patterns"]:
                mask &= ~df[text_col].str.contains(pat, na=False, regex=True)
            df = df[mask]
        print(f"  过滤 {f['type']}: {before} → {len(df)}")

    df = df.reset_index(drop=True)
    out_path = out_dir / "filtered.parquet"
    df.to_parquet(out_path)
    print(f"  ✓ {out_path}: {len(df)} 行")
    return out_path


# ============================================================================
# Stage 2: persona_generate (Claude)
# ============================================================================
def build_indexes(df: pd.DataFrame, cfg: dict) -> tuple[dict, dict]:
    cols = cfg.get("optional_columns", {})
    id_col = cols.get("id")
    parent_col = cols.get("parent_id")
    post_col = cols.get("post_id")
    title_col = cols.get("title")
    text_col = cfg["text_column"]

    by_id, by_post = {}, {}
    for _, r in df.iterrows():
        rec = {
            "text": str(r[text_col]) if pd.notna(r[text_col]) else "",
            "title": str(r[title_col]) if title_col and pd.notna(r.get(title_col)) else "",
            "parent_id": r[parent_col] if parent_col and pd.notna(r.get(parent_col)) else None,
            "post_id": r[post_col] if post_col and pd.notna(r.get(post_col)) else None,
        }
        if id_col and pd.notna(r.get(id_col)):
            by_id[r[id_col]] = rec
        if post_col and pd.notna(r.get(post_col)):
            by_post.setdefault(r[post_col], rec)
    return by_id, by_post


def assemble_context(rec: dict, by_id: dict, by_post: dict, cfg: dict) -> str:
    parts = []
    pg = cfg.get("persona_generation", {})
    max_post = pg.get("max_chars_post_body", 600)
    max_parent = pg.get("max_chars_parent", 300)

    post_id = rec.get("post_id")
    if post_id and post_id in by_post:
        post = by_post[post_id]
        if post.get("title"):
            parts.append(f"原帖标题: {post['title']}")
        body = (post.get("text") or "")[:max_post]
        if body:
            parts.append(f"原帖正文: {body}")

    parent_id = rec.get("parent_id")
    if parent_id and parent_id != post_id and parent_id in by_id:
        pbody = (by_id[parent_id]["text"] or "")[:max_parent]
        if pbody:
            parts.append(f"父评论: {pbody}")

    return "\n".join(parts) if parts else "(无上下文)"


async def call_claude_persona(prompt: str, cfg: dict) -> str:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
    pg = cfg["persona_generation"]
    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
        model=pg["model"],
        extra_args={"effort": pg.get("effort", "high")},
    )
    chunks = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks).strip()


def clean_persona(text: str) -> str:
    text = text.strip()
    cut_markers = ["**6维度", "**维度", "维度分析:", "维度分析：", "## ", "**1. ", "\n\n1. "]
    for m in cut_markers:
        idx = text.find(m)
        if idx > 50:
            text = text[:idx].rstrip()
            break
    return text


async def stage_persona(cfg: dict, filtered_path: Path, out_dir: Path) -> Path:
    print("\n=== Stage 2: Persona 生成 (Claude) ===")
    import anyio

    df = pd.read_parquet(filtered_path)
    text_col = cfg["text_column"]
    id_col = cfg.get("optional_columns", {}).get("id")

    template = (PROMPTS_DIR / "persona.md").read_text()
    by_id, by_post = build_indexes(df, cfg)

    progress_path = out_dir / "personas_progress.parquet"
    out_path = out_dir / "personas.parquet"

    done = {}
    if progress_path.exists():
        prev = pd.read_parquet(progress_path)
        done = dict(zip(prev["__row_idx"], prev["persona"]))
        print(f"  断点续跑: 已完成 {len(done)} 条")

    todo = [(i, r) for i, r in df.iterrows() if i not in done]
    print(f"  待处理 {len(todo)} 条 / 总 {len(df)}")

    pg = cfg["persona_generation"]
    workers = pg.get("workers", 2)
    sem = anyio.Semaphore(workers)
    counter = {"n": 0}
    lock = anyio.Lock()
    start = time.time()

    async def gen_one(idx, row):
        text = str(row[text_col])[:2000]
        rec = by_id.get(row[id_col]) if id_col else None
        ctx = assemble_context(rec, by_id, by_post, cfg) if rec else "(无上下文)"
        prompt = template.format(
            product_name=cfg.get("product_name", "通用产品"),
            product_category=cfg.get("product_category", "通用品类"),
            context_block=ctx,
            comment_body=text,
        )
        async with sem:
            try:
                persona = await call_claude_persona(prompt, cfg)
                persona = clean_persona(persona)
                if len(persona) < 30:
                    persona = ""
            except Exception as e:
                print(f"  ✗ idx={idx} 失败: {str(e)[:80]}")
                persona = ""
            async with lock:
                counter["n"] += 1
                done[idx] = persona
                if counter["n"] % 20 == 0:
                    pd.DataFrame([
                        {"__row_idx": k, "persona": v} for k, v in done.items()
                    ]).to_parquet(progress_path)
                elapsed = time.time() - start
                rate = counter["n"] / elapsed if elapsed > 0 else 0
                print(f"  [{counter['n']}/{len(todo)}] idx={idx} ({rate:.2f}/s)")

    async with anyio.create_task_group() as tg:
        for idx, row in todo:
            tg.start_soon(gen_one, idx, row)

    df["persona"] = df.index.map(lambda i: done.get(i, ""))
    df.to_parquet(out_path)
    if progress_path.exists():
        progress_path.unlink()
    print(f"  ✓ {out_path}: {(df['persona'] != '').sum()} 有效 persona")
    return out_path


# ============================================================================
# Stage 3: embed
# ============================================================================
def stage_embed(cfg: dict, persona_path: Path, out_dir: Path) -> Path:
    print("\n=== Stage 3: Embedding ===")
    df = pd.read_parquet(persona_path)
    df = df[df["persona"].notna() & (df["persona"].str.len() > 30)].reset_index(drop=True)
    texts = df["persona"].astype(str).tolist()

    emb_cfg = cfg["embedding"]
    provider = emb_cfg["provider"]
    print(f"  provider={provider}, model={emb_cfg['model']}, {len(texts)} 条")

    out_path = out_dir / "embeddings.npy"
    if provider == "openai":
        embeddings = embed_openai(texts, emb_cfg)
    elif provider == "voyage":
        embeddings = embed_voyage(texts, emb_cfg)
    elif provider == "gemini":
        embeddings = embed_gemini(texts, emb_cfg)
    else:
        sys.exit(f"✗ 未知 provider: {provider}")

    np.save(out_path, embeddings)
    df.to_parquet(out_dir / "personas_for_embed.parquet")
    print(f"  ✓ {out_path}: {embeddings.shape}")
    return out_path


def embed_openai(texts: list[str], cfg: dict) -> np.ndarray:
    from openai import OpenAI
    client = OpenAI(api_key=get_api_key(cfg["api_key_env"]))
    bs = cfg.get("batch_size", 100)
    max_chars = cfg.get("max_chars", 2000)
    texts = [t[:max_chars] for t in texts]
    out = []
    for i in range(0, len(texts), bs):
        batch = texts[i:i+bs]
        r = client.embeddings.create(model=cfg["model"], input=batch)
        out.extend(d.embedding for d in r.data)
        print(f"    [{i+len(batch)}/{len(texts)}]")
    return np.array(out)


def embed_voyage(texts: list[str], cfg: dict) -> np.ndarray:
    import voyageai
    client = voyageai.Client(api_key=get_api_key(cfg["api_key_env"]))
    bs = cfg.get("batch_size", 15)
    sleep_s = cfg.get("sleep_sec", 35)
    max_chars = cfg.get("max_chars", 2000)
    texts = [t[:max_chars] for t in texts]
    out = []
    for i in range(0, len(texts), bs):
        batch = texts[i:i+bs]
        for attempt in range(5):
            try:
                r = client.embed(batch, model=cfg["model"], input_type="document")
                out.extend(r.embeddings)
                break
            except Exception as e:
                wait = 30 * (attempt + 1)
                print(f"    voyage 失败, 睡 {wait}s ({e})")
                time.sleep(wait)
        if i + bs < len(texts):
            time.sleep(sleep_s)
        print(f"    [{i+len(batch)}/{len(texts)}]")
    return np.array(out)


def embed_gemini(texts: list[str], cfg: dict) -> np.ndarray:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=get_api_key(cfg["api_key_env"]))
    bs = cfg.get("batch_size", 30)
    sleep_s = cfg.get("sleep_sec", 6)
    max_chars = cfg.get("max_chars", 2000)
    texts = [t[:max_chars] for t in texts]
    out = []
    for i in range(0, len(texts), bs):
        batch = texts[i:i+bs]
        r = client.models.embed_content(
            model=cfg["model"], contents=batch,
            config=types.EmbedContentConfig(task_type="CLUSTERING"),
        )
        out.extend(e.values for e in r.embeddings)
        if i + bs < len(texts):
            time.sleep(sleep_s)
        print(f"    [{i+len(batch)}/{len(texts)}]")
    return np.array(out)


# ============================================================================
# Stage 4: cluster (UMAP + HDBSCAN)
# ============================================================================
def stage_cluster(cfg: dict, emb_path: Path, persona_path: Path, out_dir: Path) -> Path:
    print("\n=== Stage 4: UMAP + HDBSCAN ===")
    import umap
    import hdbscan

    embeddings = np.load(emb_path)
    df = pd.read_parquet(persona_path)
    cl = cfg["clustering"]

    print(f"  UMAP {embeddings.shape} → 2D + {cl['umap']['n_components']}D")
    reducer_2d = umap.UMAP(
        n_components=2,
        n_neighbors=cl["umap"]["n_neighbors"],
        min_dist=cl["umap"]["min_dist"],
        metric=cl["umap"]["metric"],
        random_state=42,
    )
    coords_2d = reducer_2d.fit_transform(embeddings)

    reducer_nd = umap.UMAP(
        n_components=cl["umap"]["n_components"],
        n_neighbors=cl["umap"]["n_neighbors"],
        min_dist=cl["umap"]["min_dist"],
        metric=cl["umap"]["metric"],
        random_state=42,
    )
    coords_nd = reducer_nd.fit_transform(embeddings)

    print(f"  HDBSCAN min_cluster_size={cl['hdbscan']['min_cluster_size']}")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=cl["hdbscan"]["min_cluster_size"],
        metric=cl["hdbscan"]["metric"],
    )
    labels = clusterer.fit_predict(coords_nd)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  → {n_clusters} 簇 + {n_noise} noise ({100*n_noise/len(labels):.1f}%)")

    df["umap_2d_x"] = coords_2d[:, 0]
    df["umap_2d_y"] = coords_2d[:, 1]
    df["hdbscan_id"] = labels

    np.save(out_dir / "umap_nd.npy", coords_nd)
    out_path = out_dir / "clusters.parquet"
    df.to_parquet(out_path)
    print(f"  ✓ {out_path}")
    return out_path


# ============================================================================
# Stage 5: meta_ward — Ward 质心层级合并 (生成全档 k=2..N)
# ============================================================================
def stage_meta_ward(cfg: dict, clusters_path: Path, out_dir: Path) -> Path:
    print("\n=== Stage 5: Ward 质心层级合并 (全档 k=2..N) ===")
    from scipy.cluster.hierarchy import linkage, fcluster

    df = pd.read_parquet(clusters_path)
    coords_nd = np.load(out_dir / "umap_nd.npy")
    labels = df["hdbscan_id"].to_numpy()

    valid_ids = sorted(set(labels[labels != -1]))
    n = len(valid_ids)
    if n < 2:
        sys.exit(f"✗ 仅 {n} 个有效细簇, 无法做 Ward 合并")

    centroids = np.array([coords_nd[labels == c].mean(axis=0) for c in valid_ids])
    print(f"  {n} 个细簇 → 算质心 → linkage")

    Z = linkage(centroids, method=cfg["meta_merge"]["ward"]["linkage_method"], metric="euclidean")
    np.save(out_dir / "ward_linkage.npy", Z)

    mapping_df = pd.DataFrame([{"original_cluster": c} for c in valid_ids])

    # 全档 k = 2 .. n (每档都生成 ward_meta_k 列)
    for k in range(2, n + 1):
        meta = fcluster(Z, t=k, criterion="maxclust")
        col = f"ward_meta_{k}"
        mapping_df[col] = meta
        cid_to_meta = dict(zip(valid_ids, meta))
        df[col] = df["hdbscan_id"].map(lambda c: int(cid_to_meta[c]) if c in cid_to_meta else -1)

    print(f"  生成 ward_meta_2 .. ward_meta_{n} 共 {n - 1} 档")

    # 报告里 highlight 的几档 (config.levels) 单独打印
    for k in cfg["meta_merge"]["ward"].get("levels", []):
        col = f"ward_meta_{k}"
        if col in mapping_df.columns:
            print(f"    [highlight] k={k}: {mapping_df[col].nunique()} 个 meta 组")

    mapping_df.to_csv(out_dir / "meta_clusters_ward.csv", index=False)
    df.to_parquet(clusters_path)
    print(f"  ✓ {out_dir / 'meta_clusters_ward.csv'}")
    return out_dir / "meta_clusters_ward.csv"


# ============================================================================
# Stage 6: meta_llm — 全档 k=2..N 逐档命名 (父档术语注入)
# ============================================================================
async def stage_meta_llm(cfg: dict, clusters_path: Path, out_dir: Path) -> Path:
    print("\n=== Stage 6: LLM 全档命名 (k=2..N, 父档术语注入) ===")
    df = pd.read_parquet(clusters_path)
    labels = df["hdbscan_id"].to_numpy()
    valid_ids = sorted(set(int(c) for c in labels[labels != -1]))
    n = len(valid_ids)
    sizes = {c: int((labels == c).sum()) for c in valid_ids}

    # 每细簇取代表 persona (按 UMAP nD 中心距离排序)
    coords_nd = np.load(out_dir / "umap_nd.npy")
    n_per = cfg["meta_merge"]["llm"].get("personas_per_cluster", 3)
    cluster_personas: dict[int, list[str]] = {}
    for c in valid_ids:
        mask = labels == c
        sub_coords = coords_nd[mask]
        center = sub_coords.mean(axis=0)
        dists = np.linalg.norm(sub_coords - center, axis=1)
        top_idx = np.argsort(dists)[:n_per]
        sub_df = df[mask].reset_index(drop=True)
        cluster_personas[c] = [str(sub_df.iloc[i]["persona"])[:200] for i in top_idx]

    template = (PROMPTS_DIR / "meta_merge.md").read_text()
    llm_cfg = cfg["meta_merge"]["llm"]
    max_k_cfg = llm_cfg.get("max_k")
    max_k = min(int(max_k_cfg), n) if max_k_cfg else n
    print(f"  细簇 N={n}, 全档 k=2..{max_k} (共 {max_k - 1} 档 LLM 调用)")
    print(f"  模型 {llm_cfg['model']} effort={llm_cfg.get('effort', 'medium')}")

    # 断点续跑
    progress_path = out_dir / "meta_ward_labels_progress.json"
    all_labels: dict = {}
    if progress_path.exists():
        all_labels = json.loads(progress_path.read_text())
        print(f"  断点: 已完成 k={[k for k in all_labels.keys()]}")

    prev_labels: dict | None = None  # k-1 档的 {ward_id: name}
    cid_first_row = {c: df[df["hdbscan_id"] == c].iloc[0] for c in valid_ids}

    for k in range(2, max_k + 1):
        key = f"k={k}"
        col = f"ward_meta_{k}"
        if col not in df.columns:
            print(f"  ⚠ {col} 缺失, 跳过")
            continue

        # 每个 ward 组的成员 (hdbscan ids)
        ward_to_members: dict[int, list[int]] = {}
        for cid in valid_ids:
            wid = int(cid_first_row[cid][col])
            ward_to_members.setdefault(wid, []).append(cid)

        # 已经标过 → 重建 prev_labels 跳过
        if key in all_labels:
            prev_labels = {item["id"]: item["name"] for item in all_labels[key]["labels"]}
            # 同时回写 df 列
            wid_to_name = prev_labels
            df[f"llm_label_k{k}"] = df[col].map(
                lambda w: wid_to_name.get(int(w), "noise") if w != -1 else "noise"
            )
            print(f"  跳过 k={k} (progress 已有)")
            continue

        # 构造 summaries
        summaries = []
        for wid in sorted(ward_to_members.keys()):
            members = ward_to_members[wid]
            total_n = sum(sizes[c] for c in members)
            sample_personas: list[str] = []
            # 按成员细簇均摊取 persona, 总数不超过 n_per
            for c in members:
                sample_personas.extend(cluster_personas[c][:2])
                if len(sample_personas) >= n_per:
                    break
            sample_personas = sample_personas[:n_per]
            block = (
                f"== ward 组 {wid} ({len(members)} 个细簇 / {total_n} 人, 细簇 ids: {members}) ==\n"
            )
            for i, p in enumerate(sample_personas, 1):
                block += f"  [{i}] {p}\n"
            summaries.append(block)

        # 父档命名注入 (k>2 时)
        parent_context = ""
        parent_map: dict[int, int] = {}
        if k > 2 and prev_labels is not None:
            parent_col = f"ward_meta_{k - 1}"
            for wid, members in ward_to_members.items():
                first_cid = members[0]
                parent_wid = int(cid_first_row[first_cid][parent_col])
                parent_map[wid] = parent_wid

            parent_context = f"\n\n【上一档 k={k - 1} 的命名 (维持术语一致)】\n"
            for pid in sorted(set(parent_map.values())):
                parent_context += f"  父{pid}: {prev_labels.get(pid, '?')}\n"
            parent_context += f"\n【本档每个 ward 组从哪个父 split 出来】\n"
            for wid in sorted(parent_map.keys()):
                pid = parent_map[wid]
                parent_context += (
                    f"  ward 组 {wid} ← 父{pid} ({prev_labels.get(pid, '?')})\n"
                )

        prompt = template.format(
            product_name=cfg.get("product_name", "通用产品"),
            target_k=str(k),
            cluster_summaries="\n".join(summaries),
            parent_context=parent_context,
        )

        print(f"\n  ── k={k} 标 {len(ward_to_members)} 组 ──")
        try:
            raw = await call_claude_meta(prompt, cfg)
        except Exception as e:
            print(f"    ✗ Claude 调用失败 k={k}: {str(e)[:120]}")
            continue
        (out_dir / f"meta_llm_raw_k{k}.txt").write_text(raw)

        try:
            data = parse_llm_json(raw)
        except Exception as e:
            print(f"    ✗ 解析失败 k={k}: {str(e)[:120]}")
            continue

        labeled = []
        for mc in data.get("meta_clusters", []):
            try:
                wid = int(mc["id"])
            except (KeyError, ValueError, TypeError):
                continue
            if wid not in ward_to_members:
                print(f"    ⚠ 无效 id={wid}, 跳过")
                continue
            labeled.append({
                "id": wid,
                "name": str(mc.get("name", f"ward{wid}")),
                "rationale": str(mc.get("rationale", "")),
                "size": sum(sizes[c] for c in ward_to_members[wid]),
                "hdbscan_members": ward_to_members[wid],
            })

        if not labeled:
            print(f"    ✗ k={k} 无有效命名, 跳过")
            continue

        entry: dict = {"labels": labeled}
        if parent_map:
            entry["parents"] = {
                str(wid): {
                    "parent_id": pid,
                    "parent_name": prev_labels.get(pid, "?") if prev_labels else "?",
                }
                for wid, pid in parent_map.items()
            }
        all_labels[key] = entry

        wid_to_name = {item["id"]: item["name"] for item in labeled}
        prev_labels = wid_to_name
        df[f"llm_label_k{k}"] = df[col].map(
            lambda w: wid_to_name.get(int(w), "noise") if w != -1 else "noise"
        )

        progress_path.write_text(json.dumps(all_labels, ensure_ascii=False, indent=2))
        for item in labeled:
            print(f"    {item['id']:>3} \"{item['name']}\" (n={item['size']})")

    # 写最终输出
    out_json = out_dir / "meta_ward_labels.json"
    summary = {
        "n_细簇": n,
        "k_max": max_k,
        "k_labeled": sorted(int(k.split("=")[1]) for k in all_labels.keys()),
        "levels_highlight": cfg["meta_merge"]["ward"].get("levels", []),
        "by_k": all_labels,
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    # 把"highlight 中位档"作为 llm_meta_id / llm_meta_name 主默认 (兼容下游)
    levels = cfg["meta_merge"]["ward"].get("levels", [])
    valid_levels = [k for k in levels if f"k={k}" in all_labels]
    default_k = valid_levels[len(valid_levels) // 2] if valid_levels else (
        sorted(int(k.split("=")[1]) for k in all_labels.keys())[0] if all_labels else None
    )
    if default_k is not None:
        df["llm_meta_id"] = df[f"ward_meta_{default_k}"]
        df["llm_meta_name"] = df[f"llm_label_k{default_k}"]
        print(f"\n  默认 highlight: k={default_k}")

    df.to_parquet(clusters_path)
    if progress_path.exists():
        progress_path.unlink()
    print(f"  ✓ {out_json} (共 {len(all_labels)} 档)")
    return out_json


def parse_llm_json(raw: str) -> dict:
    """鲁棒地从 LLM 输出抽 JSON. 容错: markdown 代码块 / 中文标点 / 末尾逗号."""
    # 1. 去掉 markdown 代码块包裹
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```\s*$", "", s)

    # 2. 找 {...} 主体
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        raise ValueError(f"找不到 JSON 块: {raw[:300]}")
    s = m.group(0)

    # 3. 直接解析
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # 4. 把字符串值里嵌套的 ASCII 双引号 (LLM 在中文 rationale 里写 "DIY" 这种) 转成
    #    中文全角双引号, 防止破坏 JSON 结构. 规则: 仅当 " 两侧都是非 ASCII 字符时替换
    s_quote_fixed = re.sub(r'(?<=[^\x00-\x7F])"(?=[^\x00-\x7F])', "”", s)
    try:
        return json.loads(s_quote_fixed)
    except json.JSONDecodeError:
        pass

    # 5. 兜底: 中文全角标点 → 半角, 去尾随逗号
    s2 = (
        s_quote_fixed.replace("，", ",")          # 全角逗号 → 半角
         .replace("：", ":")                      # 全角冒号 → 半角
         .replace("‘", "'").replace("’", "'")  # 全角单引号 → 半角
    )
    s2 = re.sub(r",(\s*[}\]])", r"\1", s2)  # 去对象/数组末尾逗号
    try:
        return json.loads(s2)
    except json.JSONDecodeError:
        pass

    # 6. 最后兜底: ast.literal_eval (允许 Python 风格的字典)
    import ast
    try:
        return ast.literal_eval(s2)
    except Exception as e:
        raise ValueError(f"所有解析策略均失败. 原始返回头 500 字: {raw[:500]}") from e


async def call_claude_meta(prompt: str, cfg: dict) -> str:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
    llm = cfg["meta_merge"]["llm"]
    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],
        model=llm["model"],
        extra_args={"effort": llm.get("effort", "high")},
    )
    chunks = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks).strip()


# ============================================================================
# Stage 7: visualize
# ============================================================================
def stage_visualize(cfg: dict, clusters_path: Path, out_dir: Path) -> None:
    print("\n=== Stage 7: 可视化 ===")
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    from scipy.cluster.hierarchy import dendrogram

    rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "Arial Unicode MS"]
    rcParams["axes.unicode_minus"] = False

    df = pd.read_parquet(clusters_path)
    Z = np.load(out_dir / "ward_linkage.npy")

    fig, ax = plt.subplots(figsize=(20, 8))
    sizes = df[df["hdbscan_id"] != -1]["hdbscan_id"].value_counts()
    valid_ids = sorted(sizes.index)
    labels_d = [f"C{c}({sizes[c]})" for c in valid_ids]
    dendrogram(Z, labels=labels_d, ax=ax, leaf_rotation=90, leaf_font_size=8)
    ax.set_title(f"Ward 层级合并 dendrogram ({cfg.get('product_name', '通用')})", fontsize=12)
    plt.tight_layout()
    plt.savefig(out_dir / "dendrogram.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out_dir / 'dendrogram.png'}")

    fig, ax = plt.subplots(figsize=(12, 9))
    noise = df["llm_meta_id"] == -1
    ax.scatter(df.loc[noise, "umap_2d_x"], df.loc[noise, "umap_2d_y"],
               s=3, alpha=0.3, c="lightgray", label="noise")
    if (~noise).any():
        ax.scatter(df.loc[~noise, "umap_2d_x"], df.loc[~noise, "umap_2d_y"],
                   s=4, alpha=0.8, c=df.loc[~noise, "llm_meta_id"], cmap="tab20")
    ax.set_title(f"UMAP 2D (LLM meta 着色) — {cfg.get('product_name', '通用')}")
    ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(out_dir / "scatter.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out_dir / 'scatter.png'}")


# ============================================================================
# Stage 8: report — 全档命名汇总 + highlight 详细展开
# ============================================================================
def stage_report(cfg: dict, clusters_path: Path, out_dir: Path) -> None:
    print("\n=== Stage 8: 综合报告 ===")

    df = pd.read_parquet(clusters_path)
    n_total = len(df)
    n_noise = int((df["hdbscan_id"] == -1).sum())
    n_clusters = df["hdbscan_id"].nunique() - (1 if -1 in df["hdbscan_id"].values else 0)

    labels_json = out_dir / "meta_ward_labels.json"
    if not labels_json.exists():
        print(f"  ⚠ {labels_json} 不存在, 跳过 report")
        return
    labels_data = json.loads(labels_json.read_text())
    by_k: dict = labels_data.get("by_k", {})
    levels_highlight = labels_data.get("levels_highlight", []) or cfg["meta_merge"]["ward"].get("levels", [])
    k_labeled = labels_data.get("k_labeled", [])

    lines = [
        f"# {cfg.get('product_name', '通用产品')} — 客户画像聚类报告",
        "",
        f"**输入**: {cfg['input_csv']} ({n_total} 条 persona)",
        f"**embedding**: {cfg['embedding']['provider']} / {cfg['embedding']['model']}",
        f"**LLM**: {cfg['meta_merge']['llm']['model']} (effort={cfg['meta_merge']['llm'].get('effort', 'medium')})",
        "",
        "## 全档画像粒度概览",
        "",
        f"- 细粒度 (HDBSCAN 自然簇): **{n_clusters}** 簇",
        f"- Noise: **{n_noise}** ({100 * n_noise / n_total:.1f}%) — 边缘评论, 不强分类",
        f"- LLM 已命名档位: **k=[{', '.join(str(k) for k in k_labeled)}]** (共 {len(k_labeled)} 档)",
        f"- 推荐高亮档 (config.levels): **k=[{', '.join(str(k) for k in levels_highlight)}]**",
        "",
        "## 各档命名一览 (粗→细)",
        "",
        "| k | 各组业务命名 (size) |",
        "|---|---|",
    ]
    for k in sorted(k_labeled):
        entry = by_k.get(f"k={k}", {})
        items = entry.get("labels", [])
        cell = " / ".join(f"{x['name']}({x['size']})" for x in sorted(items, key=lambda x: -x["size"]))
        lines.append(f"| {k} | {cell} |")

    # Highlight 档详细展开
    for k in levels_highlight:
        entry = by_k.get(f"k={k}")
        if not entry:
            continue
        items = sorted(entry["labels"], key=lambda x: -x["size"])
        lines += [
            "",
            f"## 高亮档 k={k} 详细",
            "",
            "| id | 业务名 | 人数 | 占比 | 含细簇 |",
            "|---|---|---|---|---|",
        ]
        for x in items:
            lines.append(
                f"| {x['id']} | **{x['name']}** | {x['size']} | "
                f"{100 * x['size'] / n_total:.1f}% | {x['hdbscan_members']} |"
            )
        lines += ["", "### 合并理由", ""]
        for x in items:
            lines.append(f"- **{x['name']}**: {x.get('rationale', '')}")

        # 父档命名链 (如果有)
        if entry.get("parents"):
            lines += ["", "### 父档命名链 (维持术语一致性)", ""]
            parents = entry["parents"]
            for x in items:
                p = parents.get(str(x["id"]), {})
                if p:
                    lines.append(f"- {x['name']} ← 父 {p.get('parent_name', '?')} (k={k - 1})")

    lines += [
        "",
        "## 输出物",
        "",
        "- `clusters.parquet` — 每条 persona + 全档 ward_meta_k + llm_label_k 标签",
        "- `meta_clusters_ward.csv` — 细簇 → 各档 ward_meta_k 映射",
        "- `meta_ward_labels.json` — **全档 LLM 命名** (核心交付)",
        "- `meta_llm_raw_k*.txt` — 每档 LLM 原始返回 (debug)",
        "- `dendrogram.png` — Ward 层级树",
        "- `scatter.png` — UMAP 2D 散点 (默认高亮档着色)",
        "",
        "## 业务用法",
        "",
        "1. **战略级 (老板视图)**: 看 k=2/3 档, 拿 2-3 个业务名总结全市场",
        "2. **业务报告 / PPT**: 看 highlight 档 (config.levels 默认中位), 5-15 个画像",
        "3. **长尾营销 / segment 测试**: 看 k=N 全细档, 30+ 小众画像",
        "4. **跨档下钻**: 沿父档命名链, 从粗到细给业务方讲故事",
    ]

    out_path = out_dir / "report.md"
    out_path.write_text("\n".join(lines))
    print(f"  ✓ {out_path}")
    print(f"  全档命名: k=[{', '.join(str(k) for k in k_labeled)}]")


# ============================================================================
# Main orchestrator
# ============================================================================
ALL_STAGES = ["load_filter", "persona", "embed", "cluster", "meta_ward", "meta_llm", "visualize", "report"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="yaml 配置文件路径")
    parser.add_argument("--preset", help="预设名 (从 config 的 presets 加载)")
    parser.add_argument(
        "--stages", default=",".join(ALL_STAGES),
        help=f"逗号分隔的阶段名, 可选: {','.join(ALL_STAGES)}",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config), preset=args.preset)
    out_dir = Path(cfg["output_dir"])
    ensure_dir(out_dir)
    stages = args.stages.split(",")

    paths = {
        "filtered": out_dir / "filtered.parquet",
        "personas": out_dir / "personas.parquet",
        "embeddings": out_dir / "embeddings.npy",
        "personas_for_embed": out_dir / "personas_for_embed.parquet",
        "clusters": out_dir / "clusters.parquet",
    }

    if "load_filter" in stages:
        stage_load_filter(cfg, out_dir)
    if "persona" in stages:
        asyncio.run(stage_persona(cfg, paths["filtered"], out_dir))
    if "embed" in stages:
        stage_embed(cfg, paths["personas"], out_dir)
    if "cluster" in stages:
        stage_cluster(cfg, paths["embeddings"], paths["personas_for_embed"], out_dir)
    if "meta_ward" in stages:
        stage_meta_ward(cfg, paths["clusters"], out_dir)
    if "meta_llm" in stages:
        asyncio.run(stage_meta_llm(cfg, paths["clusters"], out_dir))
    if "visualize" in stages:
        stage_visualize(cfg, paths["clusters"], out_dir)
    if "report" in stages:
        stage_report(cfg, paths["clusters"], out_dir)

    print("\n=== Pipeline 完成 ===")
    print(f"  → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
