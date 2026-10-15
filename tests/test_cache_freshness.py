import os
import pickle

from obsidian_vault_graph.cli import load_graph_cached


def test_edit_of_older_note_invalidates_cache(tmp_path):
    a, b, c = (tmp_path / f"{name}.md" for name in "abc")
    a.write_text("[[b]]")
    b.write_text("")
    c.write_text("")
    os.utime(a, ns=(100, 100))
    os.utime(c, ns=(300, 300))
    load_graph_cached(tmp_path, use_cache=True)
    a.write_text("[[c]]")
    os.utime(a, ns=(200, 200))
    assert load_graph_cached(tmp_path, use_cache=True)[1]["a.md"] == {"c.md"}


def test_same_size_rename_invalidates_cache(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("hello")
    load_graph_cached(tmp_path, use_cache=True)
    a.rename(tmp_path / "b.md")
    assert set(load_graph_cached(tmp_path, use_cache=True)[0]) == {"b.md"}


def test_previous_parser_cache_is_rebuilt(tmp_path):
    (tmp_path / "a.md").write_text("`[[b]]`")
    (tmp_path / "b.md").write_text("")
    load_graph_cached(tmp_path, use_cache=True)
    cache = tmp_path / ".hermes" / "vault_graph_cache_all.pkl"
    payload = pickle.loads(cache.read_bytes())
    payload["fingerprint"].pop("parser_version")
    payload["graph"][1]["a.md"] = {"b.md"}
    cache.write_bytes(pickle.dumps(payload))
    assert load_graph_cached(tmp_path, use_cache=True)[1]["a.md"] == set()
