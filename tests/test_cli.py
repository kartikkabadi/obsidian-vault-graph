from pathlib import Path

from obsidian_vault_graph.cli import load_graph, obsidian_uri


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_graph_resolves_aliases_and_links(tmp_path):
    write(tmp_path / "wiki" / "alpha.md", "---\ntitle: Alpha Note\naliases: [A]\ntags: [hub]\n---\n# Alpha\nLinks to [[Beta]] and [[Gamma|G]]. #inline\n")
    write(tmp_path / "wiki" / "beta.md", "# Beta\nBack to [[A]].\n")
    write(tmp_path / "wiki" / "gamma.md", "# Gamma\n")

    notes, out_edges, in_edges, broken, unresolved, resolve = load_graph(tmp_path, "wiki")

    assert len(notes) == 3
    assert resolve("A") == "wiki/alpha.md"
    assert resolve("Alpha Note") == "wiki/alpha.md"
    assert out_edges["wiki/alpha.md"] == {"wiki/beta.md", "wiki/gamma.md"}
    assert in_edges["wiki/alpha.md"] == {"wiki/beta.md"}
    assert broken == []
    assert notes["wiki/alpha.md"].tags == ["hub", "inline"]


def test_broken_links_are_reported(tmp_path):
    write(tmp_path / "note.md", "See [[Missing Page]].")
    notes, out_edges, in_edges, broken, unresolved, resolve = load_graph(tmp_path)
    assert broken == [{"source": "note.md", "target": "Missing Page"}]
    assert unresolved["Missing Page"] == 1


def test_obsidian_uri_encodes_vault_and_file(tmp_path):
    vault = tmp_path / "My Vault"
    vault.mkdir()
    uri = obsidian_uri(vault, "wiki/my note.md")
    assert uri == "obsidian://open?vault=My%20Vault&file=wiki/my%20note"
