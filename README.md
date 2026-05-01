# Obsidian Vault Graph

A local, zero-dependency CLI for turning an Obsidian vault into a useful knowledge graph.

It parses Markdown files and Obsidian wikilinks to answer graph questions like:

- What links to this note?
- What does this note link out to?
- What are the central hub notes?
- Which notes are orphans?
- Which wikilinks are broken?
- What bridge path connects two ideas?
- Can I turn a neighborhood into a Mermaid graph?
- Can I combine QMD retrieval with graph expansion?

The CLI is designed to pair well with [QMD](https://github.com/tobi/qmd): QMD retrieves relevant notes by text/semantics; `vault-graph` expands the structural context around them.

## Install

With `pipx`:

```bash
pipx install git+https://github.com/kartikkabadi/obsidian-vault-graph.git
```

With `pip`:

```bash
python3 -m pip install --user git+https://github.com/kartikkabadi/obsidian-vault-graph.git
```

From a local clone:

```bash
git clone https://github.com/kartikkabadi/obsidian-vault-graph.git
cd obsidian-vault-graph
python3 -m pip install -e .
```

One-line installer:

```bash
curl -fsSL https://raw.githubusercontent.com/kartikkabadi/obsidian-vault-graph/main/scripts/install.sh | bash
```

Install the included Hermes Agent skill too:

```bash
curl -fsSL https://raw.githubusercontent.com/kartikkabadi/obsidian-vault-graph/main/scripts/install.sh | bash -s -- --with-skill
```

## Configure

Point the CLI at your vault:

```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/Obsidian Vault"
```

Or pass it explicitly:

```bash
vault-graph --vault "/path/to/your/Obsidian Vault" status
```

If neither `OBSIDIAN_VAULT_PATH` nor `WIKI_PATH` is set, it falls back to:

```text
~/Documents/Obsidian Vault
```

## Quick Start

```bash
vault-graph status
vault-graph --scope wiki status
vault-graph --scope wiki centrality --limit 25
vault-graph --scope wiki backlinks "My Note"
vault-graph --scope wiki links "My Note"
vault-graph --scope wiki neighbors "My Note" --depth 2
vault-graph --scope wiki bridge "Idea A" "Idea B"
vault-graph --scope wiki broken --group
vault-graph --scope wiki orphans
vault-graph --scope wiki tags
vault-graph --scope wiki mermaid "My Note"
vault-graph --scope wiki uri "My Note"
```

Use cache for repeated queries:

```bash
vault-graph --scope wiki --cache centrality --limit 10
```

## QMD Hybrid Retrieval

If `qmd` is installed and configured, `qmd-topic` performs QMD search and graph-expands returned notes:

```bash
vault-graph --scope wiki qmd-topic "agent memory systems" --qmd-limit 5 --neighbor-limit 10
```

Plain graph commands do not require QMD.

## What It Parses

- `[[wikilinks]]`
- `[[Note#Heading|Alias]]`
- embeds via `![[Note]]`
- frontmatter `title`
- frontmatter `aliases` / `alias`
- frontmatter `tags`
- inline tags like `#pkm`
- folders/scopes such as `wiki/` or `projects/`

## Why Scope Matters

For vaults with large raw imports, full-vault graph metrics can be noisy. Prefer a curated folder when reasoning:

```bash
vault-graph --scope wiki centrality
```

Use full-vault scans for broad hygiene and raw-to-canonical promotion analysis.

## Hermes Agent Skill

This repo includes a Hermes Agent skill at:

```text
skills/obsidian-knowledge-graph/SKILL.md
```

Install it manually:

```bash
mkdir -p ~/.hermes/skills/note-taking/obsidian-knowledge-graph
curl -fsSL https://raw.githubusercontent.com/kartikkabadi/obsidian-vault-graph/main/skills/obsidian-knowledge-graph/SKILL.md \
  -o ~/.hermes/skills/note-taking/obsidian-knowledge-graph/SKILL.md
```

Or use the installer with `--with-skill`.

## Examples

Find hub notes:

```bash
vault-graph --scope wiki centrality --limit 10
```

Find broken canonical pages to create or alias:

```bash
vault-graph --scope wiki broken --group --limit 25
```

Find a two-hop context neighborhood:

```bash
vault-graph --scope wiki neighbors "Hermes Agent" --depth 2 --limit 50
```

Create a Mermaid snippet:

```bash
vault-graph --scope wiki mermaid "Hermes Agent" --limit 25
```

Open a note in Obsidian:

```bash
vault-graph --scope wiki uri "Hermes Agent"
```

## Development

```bash
git clone https://github.com/kartikkabadi/obsidian-vault-graph.git
cd obsidian-vault-graph
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[dev]'
pytest
```

## License

MIT
