#!/usr/bin/env python3
"""Lightweight Obsidian vault graph helper.

Builds a graph from markdown wikilinks, tags, and note metadata. Defaults to
$OBSIDIAN_VAULT_PATH, $WIKI_PATH, or ~/Documents/Obsidian Vault.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\]\n]+)\]\]")
EMBED_RE = re.compile(r"!\[\[([^\]\n]+)\]\]")
TAG_RE = re.compile(r"(?<![\w/])#([A-Za-z0-9_/-]+)")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

EXCLUDE_DIRS = {".git", ".obsidian", "node_modules", ".trash", ".DS_Store"}

@dataclass
class Note:
    path: str
    stem: str
    title: str
    aliases: list[str]
    tags: list[str]
    outgoing: list[str]
    embeds: list[str]


@dataclass
class Resolver:
    aliases: dict[str, list[str]]
    path_by_stem: dict[str, list[str]]
    scope: str | None = None

    def choose(self, candidates: list[str]) -> str | None:
        unique = sorted(set(candidates))
        if not unique:
            return None
        if len(unique) == 1:
            return unique[0]
        scoped = [p for p in unique if p.startswith("wiki/")]
        if len(scoped) == 1:
            return scoped[0]
        if self.scope:
            scoped = [p for p in unique if p.startswith(self.scope.rstrip("/") + "/")]
            if len(scoped) == 1:
                return scoped[0]
        return None

    def __call__(self, target: str) -> str | None:
        raw = target.strip()
        if not raw:
            return None
        raw = raw[:-3] if raw.lower().endswith(".md") else raw
        key = raw.lower()
        for candidate_key in (key, key + ".md", Path(raw).as_posix().lower(), Path(raw).as_posix().lower() + ".md"):
            hit = self.choose(self.aliases.get(candidate_key, []))
            if hit:
                return hit
        return self.choose(self.path_by_stem.get(Path(raw).stem.lower(), []))


def vault_default() -> Path:
    return Path(os.environ.get("OBSIDIAN_VAULT_PATH") or os.environ.get("WIKI_PATH") or "~/Documents/Obsidian Vault").expanduser()


def iter_markdown(vault: Path, scope: str | None = None) -> Iterable[Path]:
    root = vault / scope if scope else vault
    for p in root.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def rel(vault: Path, path: Path) -> str:
    return path.relative_to(vault).as_posix()


def split_link(raw: str) -> str:
    # [[Page#Heading|Alias]] -> Page
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    return target


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    data: dict[str, object] = {}
    key = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            k, v = line.split(":", 1)
            key = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                items = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
                data[key] = items
            elif v:
                data[key] = v.strip('"\'')
            else:
                data[key] = []
        elif key and line.strip().startswith("-"):
            cur = data.setdefault(key, [])
            if isinstance(cur, list):
                cur.append(line.strip()[1:].strip().strip('"\''))
    return data


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)] if str(value).strip() else []


def load_graph(vault: Path, scope: str | None = None):
    vault = vault.resolve()
    notes: dict[str, Note] = {}
    aliases: dict[str, list[str]] = defaultdict(list)
    path_by_stem: dict[str, list[str]] = defaultdict(list)

    for p in iter_markdown(vault, scope):
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        r = rel(vault, p)
        fm = parse_frontmatter(text)
        title = str(fm.get("title") or p.stem)
        note_aliases = as_list(fm.get("aliases")) + as_list(fm.get("alias"))
        fm_tags = [t.lstrip("#") for t in as_list(fm.get("tags"))]
        tags = sorted(set(fm_tags + TAG_RE.findall(text)))
        outgoing = [split_link(m.group(1)) for m in WIKILINK_RE.finditer(text)]
        embeds = [split_link(m.group(1)) for m in EMBED_RE.finditer(text)]
        notes[r] = Note(r, p.stem, title, note_aliases, tags, [x for x in outgoing if x], [x for x in embeds if x])
        path_by_stem[p.stem.lower()].append(r)
        for key in {p.stem, title, r, str(Path(r).with_suffix("")), p.name}:
            aliases[key.lower()].append(r)
        for a in note_aliases:
            aliases[a.lower()].append(r)

    resolve = Resolver(dict(aliases), dict(path_by_stem), scope)

    out_edges: dict[str, set[str]] = {p: set() for p in notes}
    broken: list[dict[str, str]] = []
    unresolved_counter: Counter[str] = Counter()
    for src, n in notes.items():
        for target in n.outgoing:
            dst = resolve(target)
            if dst:
                out_edges[src].add(dst)
            else:
                broken.append({"source": src, "target": target})
                unresolved_counter[target] += 1

    in_edges: dict[str, set[str]] = {p: set() for p in notes}
    for src, dsts in out_edges.items():
        for dst in dsts:
            in_edges[dst].add(src)

    return notes, out_edges, in_edges, broken, unresolved_counter, resolve


def cache_fingerprint(vault: Path, scope: str | None = None) -> dict:
    files = []
    for p in iter_markdown(vault, scope):
        try:
            st = p.stat()
        except OSError:
            continue
        files.append((rel(vault, p), st.st_mtime_ns, st.st_size))
    latest = max((mtime for _, mtime, _ in files), default=0)
    total_size = sum(size for _, _, size in files)
    return {"scope": scope, "count": len(files), "latest_mtime_ns": latest, "total_size": total_size}


def load_graph_cached(vault: Path, scope: str | None = None, use_cache: bool = False):
    if not use_cache:
        return load_graph(vault, scope)
    cache_dir = vault / ".hermes"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_scope = (scope or "all").replace("/", "_")
    cache_path = cache_dir / f"vault_graph_cache_{safe_scope}.pkl"
    fp = cache_fingerprint(vault, scope)
    if cache_path.exists():
        try:
            cached = pickle.loads(cache_path.read_bytes())
            if cached.get("fingerprint") == fp:
                return cached["graph"]
        except Exception:
            pass
    graph = load_graph(vault, scope)
    cache_path.write_bytes(pickle.dumps({"fingerprint": fp, "graph": graph}, protocol=pickle.HIGHEST_PROTOCOL))
    return graph


def find_note(query: str, notes: dict[str, Note], resolve) -> str | None:
    hit = resolve(query)
    if hit:
        return hit
    q = query.lower()
    matches = [p for p, n in notes.items() if q in p.lower() or q in n.title.lower() or q in n.stem.lower()]
    return matches[0] if len(matches) == 1 else None


def obsidian_uri(vault: Path, note_path: str) -> str:
    vault_name = vault.name
    file_no_ext = str(Path(note_path).with_suffix(""))
    return f"obsidian://open?vault={quote(vault_name)}&file={quote(file_no_ext)}"


def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_status(args, graph):
    notes, out_edges, in_edges, broken, unresolved, _ = graph
    linked = sum(len(v) for v in out_edges.values())
    tag_count = sum(len(n.tags) for n in notes.values())
    orphans = [p for p in notes if not out_edges[p] and not in_edges[p]]
    print_json({
        "vault": str(args.vault),
        "scope": args.scope,
        "notes": len(notes),
        "resolved_wikilink_edges": linked,
        "broken_wikilinks": len(broken),
        "tag_mentions": tag_count,
        "orphans": len(orphans),
    })


def cmd_backlinks(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    p = find_note(args.note, notes, resolve)
    if not p:
        raise SystemExit(f"Note not found or ambiguous: {args.note}")
    rows = sorted(in_edges[p])[: args.limit]
    print_json({"note": p, "backlinks": rows, "count": len(in_edges[p])})


def cmd_links(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    p = find_note(args.note, notes, resolve)
    if not p:
        raise SystemExit(f"Note not found or ambiguous: {args.note}")
    print_json({"note": p, "links": sorted(out_edges[p])[: args.limit], "count": len(out_edges[p])})


def cmd_neighbors(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    start = find_note(args.note, notes, resolve)
    if not start:
        raise SystemExit(f"Note not found or ambiguous: {args.note}")
    seen = {start}
    q = deque([(start, 0)])
    result = []
    while q:
        node, depth = q.popleft()
        if depth >= args.depth:
            continue
        for nb in sorted(out_edges[node] | in_edges[node]):
            if nb in seen:
                continue
            seen.add(nb)
            result.append({"note": nb, "depth": depth + 1, "in": len(in_edges[nb]), "out": len(out_edges[nb])})
            q.append((nb, depth + 1))
    print_json({"note": start, "depth": args.depth, "neighbors": result[: args.limit], "count": len(result)})


def cmd_centrality(args, graph):
    notes, out_edges, in_edges, *_ = graph
    rows = []
    for p in notes:
        rows.append({"note": p, "score": len(in_edges[p]) * 2 + len(out_edges[p]), "in": len(in_edges[p]), "out": len(out_edges[p]), "title": notes[p].title})
    rows.sort(key=lambda x: (x["score"], x["in"], x["out"]), reverse=True)
    print_json(rows[: args.limit])


def cmd_orphans(args, graph):
    notes, out_edges, in_edges, *_ = graph
    rows = [p for p in sorted(notes) if not out_edges[p] and not in_edges[p]]
    print_json({"orphans": rows[: args.limit], "count": len(rows)})


def cmd_broken(args, graph):
    _, _, _, broken, unresolved, _ = graph
    if args.group:
        rows = [{"target": t, "count": c} for t, c in unresolved.most_common(args.limit)]
        print_json(rows)
    else:
        print_json({"broken": broken[: args.limit], "count": len(broken)})


def cmd_tags(args, graph):
    notes, *_ = graph
    c = Counter(tag for n in notes.values() for tag in n.tags)
    print_json([{"tag": t, "count": n} for t, n in c.most_common(args.limit)])


def cmd_bridge(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    a = find_note(args.a, notes, resolve)
    b = find_note(args.b, notes, resolve)
    if not a or not b:
        raise SystemExit(f"Could not resolve both notes: {args.a!r}->{a}, {args.b!r}->{b}")
    adj = {p: out_edges[p] | in_edges[p] for p in notes}
    q = deque([(a, [a])])
    seen = {a}
    found = []
    while q and len(found) < args.limit:
        node, path = q.popleft()
        if len(path) - 1 > args.depth:
            continue
        if node == b:
            found.append(path)
            continue
        for nb in sorted(adj[node]):
            if nb in seen and nb != b:
                continue
            seen.add(nb)
            q.append((nb, path + [nb]))
    print_json({"a": a, "b": b, "paths": found, "count": len(found)})


def cmd_mermaid(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    p = find_note(args.note, notes, resolve)
    if not p:
        raise SystemExit(f"Note not found or ambiguous: {args.note}")
    nodes = [p] + sorted((out_edges[p] | in_edges[p]))[: args.limit]
    node_set = set(nodes)
    def label(x):
        return re.sub(r"[^A-Za-z0-9_]", "_", x)[:60]
    print("graph TD")
    for src in nodes:
        for dst in sorted(out_edges[src]):
            if dst in node_set:
                print(f'  {label(src)}["{notes[src].title}"] --> {label(dst)}["{notes[dst].title}"]')
        for dst in sorted(in_edges[src]):
            if src == p and dst in node_set:
                print(f'  {label(dst)}["{notes[dst].title}"] --> {label(src)}["{notes[src].title}"]')


def cmd_uri(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    p = find_note(args.note, notes, resolve)
    if not p:
        raise SystemExit(f"Note not found or ambiguous: {args.note}")
    print_json({"note": p, "title": notes[p].title, "uri": obsidian_uri(args.vault, p), "path": str(args.vault / p)})


def cmd_qmd_topic(args, graph):
    notes, out_edges, in_edges, broken, unresolved, resolve = graph
    cmd = ["qmd", "query", args.query, "--json", "-n", str(args.qmd_limit)]
    for collection in args.collection:
        cmd.extend(["-c", collection])
    if args.no_rerank:
        cmd.append("--no-rerank")
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    raw = proc.stdout.strip()
    start = raw.find("[")
    results = []
    if proc.returncode == 0 and start >= 0:
        try:
            results = json.loads(raw[start:])
        except json.JSONDecodeError:
            results = []
    expanded = []
    for r in results:
        file_ref = str(r.get("file", "")).replace("qmd://", "")
        note = find_note(file_ref, notes, resolve)
        if not note:
            note = find_note(Path(file_ref).stem, notes, resolve)
        if not note:
            expanded.append({"qmd": r, "note": None, "neighbors": []})
            continue
        neighbors = []
        for nb in sorted(out_edges[note] | in_edges[note])[: args.neighbor_limit]:
            neighbors.append({"note": nb, "title": notes[nb].title, "in": len(in_edges[nb]), "out": len(out_edges[nb])})
        expanded.append({
            "qmd": {"file": file_ref, "title": r.get("title"), "score": r.get("score"), "docid": r.get("docid")},
            "note": note,
            "title": notes[note].title,
            "in": len(in_edges[note]),
            "out": len(out_edges[note]),
            "neighbors": neighbors,
        })
    print_json({"query": args.query, "qmd_results": len(results), "expanded": expanded, "qmd_stderr": proc.stderr.strip() if proc.returncode else ""})


def main(argv=None):
    ap = argparse.ArgumentParser(description="Obsidian vault graph helper")
    ap.add_argument("--vault", type=Path, default=vault_default())
    ap.add_argument("--scope", help="Restrict to subfolder, e.g. wiki")
    ap.add_argument("--cache", action="store_true", help="Use persistent graph cache under .hermes/")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    for name in ["backlinks", "links", "neighbors", "mermaid", "uri"]:
        sp = sub.add_parser(name)
        sp.add_argument("note")
        sp.add_argument("--limit", type=int, default=50)
        if name == "neighbors": sp.add_argument("--depth", type=int, default=2)
    sp = sub.add_parser("centrality"); sp.add_argument("--limit", type=int, default=25)
    sp = sub.add_parser("orphans"); sp.add_argument("--limit", type=int, default=50)
    sp = sub.add_parser("broken"); sp.add_argument("--limit", type=int, default=50); sp.add_argument("--group", action="store_true")
    sp = sub.add_parser("tags"); sp.add_argument("--limit", type=int, default=50)
    sp = sub.add_parser("bridge"); sp.add_argument("a"); sp.add_argument("b"); sp.add_argument("--depth", type=int, default=4); sp.add_argument("--limit", type=int, default=5)
    sp = sub.add_parser("qmd-topic", help="Run QMD retrieval, then graph-expand returned notes")
    sp.add_argument("query")
    sp.add_argument("--collection", "-c", action="append", default=["wiki"], help="QMD collection filter; repeatable")
    sp.add_argument("--qmd-limit", type=int, default=5)
    sp.add_argument("--neighbor-limit", type=int, default=10)
    sp.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args(argv)
    args.vault = args.vault.expanduser().resolve()
    if not args.vault.exists():
        raise SystemExit(f"Vault not found: {args.vault}")
    graph = load_graph_cached(args.vault, args.scope, args.cache)
    globals()[f"cmd_{args.cmd.replace('-', '_')}"](args, graph)

if __name__ == "__main__":
    main()
