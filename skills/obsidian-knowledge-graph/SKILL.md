---
name: obsidian-knowledge-graph
description: Use when working with Kartik's Obsidian vault knowledge graph, QMD retrieval, vault-graph tooling, backlinks, centrality, broken links, or graph hygiene reports.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, qmd, knowledge-graph, backlinks, vault, pkm]
    related_skills: [obsidian]
---

# Obsidian Knowledge Graph

## Overview

Kartik's `Kartik & Hermes` vault has two complementary knowledge layers:

- **QMD** for lexical/vector/hybrid retrieval over indexed markdown collections.
- **`vault-graph`** for structural graph reasoning from Obsidian wikilinks, backlinks, tags, aliases, folders, and local paths.

Use QMD to find relevant documents by meaning. Use the graph helper to understand relationships, hubs, backlinks, neighborhoods, bridge paths, broken links, and orphan notes.

## Setup

Install the public CLI first:

```bash
pipx install git+https://github.com/kartikkabadi/obsidian-vault-graph.git
# or from a clone:
pip install -e .
```

Point it at an Obsidian vault:

```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/Obsidian Vault"
# optional fallback:
export WIKI_PATH="/path/to/your/Obsidian Vault"
```

Optional: install QMD if you want `qmd-topic` hybrid retrieval. Plain graph commands do not require QMD.

## When to Use

Use this skill when the user asks to:

- Search or reason over the Obsidian vault.
- Find backlinks, outgoing links, neighbors, graph hubs, bridges, tags, or orphans.
- Understand how QMD and the Obsidian graph relate.
- Generate or interpret vault graph health reports.
- Clean broken links or improve vault structure.
- Find canonical notes, promotion candidates, or missing hub pages.
- Use Obsidian URIs or local file paths for notes.

Do **not** use the graph as a replacement for reading source notes. The graph gives structure; QMD/filesystem reads give content.

## Preferred Workflow

1. **Start with QMD for topic discovery** when the user asks about a concept:
   - Use `mcp_qmd_query` from the agent toolset, or CLI `qmd query` when scripting.
   - Prefer `collections: ["wiki"]` for curated answers.
   - Add `scratch` only for active/provisional thinking.
   - Use raw collections only when source material is required.

2. **Graph-expand the strongest notes**:
   ```bash
   vault-graph --scope wiki backlinks "Hermes Agent" --limit 25
   vault-graph --scope wiki links "Hermes Agent" --limit 25
   vault-graph --scope wiki neighbors "Hermes Agent" --depth 2 --limit 50
   ```

3. **Use hybrid QMD + graph when the input is a topic rather than a note**:
   ```bash
   vault-graph --scope wiki qmd-topic "agent memory systems" --qmd-limit 5 --neighbor-limit 10
   ```

4. **Read central notes before answering**:
   - Use `mcp_qmd_get` for QMD result docs/docids.
   - Use filesystem reads only when path-specific inspection or edits are required.

5. **Answer with both content and structure**:
   - Content: what the notes say.
   - Structure: related notes, backlinks, hubs, missing links, or cleanup opportunities.

## Core Commands

Status:

```bash
vault-graph --scope wiki status
vault-graph --scope wiki --cache status
```

Centrality:

```bash
vault-graph --scope wiki centrality --limit 25
```

Backlinks and outgoing links:

```bash
vault-graph --scope wiki backlinks "Hermes Agent" --limit 25
vault-graph --scope wiki links "Hermes Agent" --limit 25
```

Neighborhoods:

```bash
vault-graph --scope wiki neighbors "Hermes Agent" --depth 2 --limit 50
```

Bridge paths:

```bash
vault-graph --scope wiki bridge "Hermes Agent" "LLM Wiki Pattern" --depth 4
```

Graph hygiene:

```bash
vault-graph --scope wiki orphans --limit 50
vault-graph --scope wiki broken --group --limit 25
vault-graph --scope wiki tags --limit 50
```

Mermaid graph snippets:

```bash
vault-graph --scope wiki mermaid "Hermes Agent" --limit 25
```

Obsidian URI/local path:

```bash
vault-graph --scope wiki uri "Hermes Agent"
```

QMD + graph hybrid:

```bash
vault-graph --scope wiki qmd-topic "Hermes memory providers" --qmd-limit 5 --neighbor-limit 10
```

## Current Baseline

For a healthy curated notes folder, expect:

- `status` returns a non-zero note count.
- `centrality` surfaces your main hub notes.
- `broken --group` shows missing canonical pages or aliases worth reviewing.
- `orphans` shows notes with no resolved incoming or outgoing wikilinks.

Re-check with:

```bash
vault-graph --scope wiki --cache status
```

## Scope Guidance

Prefer `--scope wiki` for reasoning. The full vault contains large raw imports and many disconnected notes, so full-vault graph metrics are noisy.

Use full-vault graph only for:

- broad hygiene audits
- raw-to-wiki promotion analysis
- finding disconnected raw source clusters
- validating total vault structure

## Cache

Use `--cache` before the subcommand for repeated graph queries:

```bash
vault-graph --scope wiki --cache centrality --limit 10
```

Cache files live in the vault's `.hermes/` directory and invalidate based on markdown count, total size, and latest modified time.

## Weekly Hygiene

For recurring hygiene, run a scheduled command in your scheduler of choice:

```bash
vault-graph --scope wiki --cache status
vault-graph --scope wiki --cache centrality --limit 10
vault-graph --scope wiki --cache broken --group --limit 10
vault-graph --scope wiki --cache orphans --limit 20
```

If you use Hermes Agent cron, point a pre-run script at those commands and ask the job to summarize graph health and cleanup actions.

## Common Pitfalls

1. **Using graph results as content evidence.** Backlinks and centrality show relationships, not claims. Read the underlying notes before answering substantive questions.

2. **Using full-vault metrics for quality judgments.** Raw imports dominate the full vault. Prefer `--scope wiki` unless raw imports are explicitly relevant.

3. **Forgetting path quoting.** The vault path contains `&`. Prefer the `vault-graph` shim instead of manual script paths.

4. **Over-cleaning broken links.** A broken link may represent an intentionally missing canonical page. Consider creating aliases/canonical pages rather than deleting links.

5. **Assuming QMD index updates automatically.** If new notes do not appear in QMD, check `mcp_qmd_status` or run the appropriate QMD update flow.

## Verification Checklist

- [ ] `vault-graph --scope wiki status` runs successfully.
- [ ] `vault-graph --scope wiki centrality --limit 3` returns `Hermes Agent` near the top unless the graph has changed materially.
- [ ] `vault-graph --scope wiki uri "Hermes Agent"` returns an `obsidian://open?...` URI.
- [ ] `mcp_qmd_status` reports `needsEmbedding: 0` or any embedding backlog is explicitly noted.
- [ ] For reports, include changed files, graph metrics, and remaining risks.
