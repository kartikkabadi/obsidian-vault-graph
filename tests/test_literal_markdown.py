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


def test_inline_code_does_not_join_unrelated_syntax(tmp_path):
    (tmp_path / "source.md").write_text("#visible`example`tail\n[`example`[Fake]]")
    (tmp_path / "Fake.md").write_text("")
    notes, outgoing, *_ = load_graph(tmp_path)
    assert not outgoing["source.md"]
    assert notes["source.md"].tags == ["visible"]


def test_invalid_backtick_fence_does_not_hide_links(tmp_path):
    (tmp_path / "source.md").write_text("```invalid`info\n[[Real]]\n")
    (tmp_path / "Real.md").write_text("")
    assert load_graph(tmp_path)[1]["source.md"] == {"Real.md"}


def test_inline_spans_cannot_bridge_blocks_or_create_links(tmp_path):
    (tmp_path / "source.md").write_text(
        "[[`code`Fake]]\n\n"
        "`unclosed\n```md\n[[Fake]]\n```\n[[Real]]\n`later\n"
        "\n> ```md\n> [[Fake]] #quoted\n> ```\n"
        "- ```md\n  [[Fake]] #listed\n  ```\n"
    )
    (tmp_path / "Real.md").write_text("")
    (tmp_path / "Fake.md").write_text("")
    notes, outgoing, *_ = load_graph(tmp_path)
    assert outgoing["source.md"] == {"Real.md"}
    assert notes["source.md"].tags == []


def test_frontmatter_code_marker_cannot_hide_markdown_body(tmp_path):
    (tmp_path / "source.md").write_text("---\ndescription: |\n  ```\n---\n[[Real]] #visible\n")
    (tmp_path / "Real.md").write_text("")
    notes, outgoing, *_ = load_graph(tmp_path)
    assert outgoing["source.md"] == {"Real.md"}
    assert notes["source.md"].tags == ["visible"]
