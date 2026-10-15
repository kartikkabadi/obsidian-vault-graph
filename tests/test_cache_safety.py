import pickle

from obsidian_vault_graph import cli


class CachePayload:
    def __init__(self, marker):
        self.marker = marker

    def __reduce__(self):
        return eval, (f"__import__('pathlib').Path({str(self.marker)!r}).write_text('executed')",)


def test_untrusted_cache_cannot_execute_code(tmp_path):
    (tmp_path / "note.md").write_text("hello")
    cache_dir = tmp_path / ".hermes"
    cache_dir.mkdir()
    marker = tmp_path / "marker"
    (cache_dir / "vault_graph_cache_all.pkl").write_bytes(pickle.dumps(CachePayload(marker)))
    assert "note.md" in cli.load_graph_cached(tmp_path, use_cache=True)[0]
    assert not marker.exists()


def test_normal_graph_cache_still_loads(tmp_path, monkeypatch):
    (tmp_path / "a.md").write_text("[[b]]")
    (tmp_path / "b.md").write_text("")
    first = cli.load_graph_cached(tmp_path, use_cache=True)
    def must_not_rebuild(*args):
        raise AssertionError("normal cache should load without rebuilding")
    monkeypatch.setattr(cli, "load_graph", must_not_rebuild)
    second = cli.load_graph_cached(tmp_path, use_cache=True)
    assert second[1] == first[1]
    assert second[-1]("a") == "a.md"
