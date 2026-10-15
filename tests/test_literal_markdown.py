from obsidian_vault_graph.cli import load_graph


def test_code_examples_do_not_create_graph_links_or_tags(tmp_path):
    (tmp_path / "source.md").write_text(
        "[[Real]] #visible\n```md\n[[Fake]] #fenced\n```\n"
        "~~~md\n[[Fake]] #tilde\n~~~\nInline `[[Fake]] #inline` example.\n"
    )
    (tmp_path / "Real.md").write_text("")
    (tmp_path / "Fake.md").write_text("")
    notes, outgoing, *_ = load_graph(tmp_path)
    assert outgoing["source.md"] == {"Real.md"}
    assert notes["source.md"].tags == ["visible"]
