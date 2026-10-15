from obsidian_vault_graph.cli import main


def test_mermaid_keeps_distinct_paths_and_escapes_titles(tmp_path, capsys):
    (tmp_path / "a-b.md").write_text("[[a_b]]")
    (tmp_path / "a_b.md").write_text('---\ntitle: A "quoted" note\n---\n')
    main(["--vault", str(tmp_path), "mermaid", "a-b"])
    output = capsys.readouterr().out
    assert 'n0["a-b"]' in output
    assert 'n1["A #quot;quoted#quot; note"]' in output
    assert "n0 --> n1" in output
    assert output.count("-->") == 1


def test_mermaid_renders_an_isolated_note(tmp_path, capsys):
    (tmp_path / "alone.md").write_text("No links")
    main(["--vault", str(tmp_path), "mermaid", "alone"])
    assert 'n0["alone"]' in capsys.readouterr().out


def test_mermaid_self_link_does_not_consume_neighbor_limit(tmp_path, capsys):
    (tmp_path / "a.md").write_text("[[a]] [[b]]")
    (tmp_path / "b.md").write_text("---\ntitle: Issue #38;\n---\n")
    main(["--vault", str(tmp_path), "mermaid", "a", "--limit", "1"])
    output = capsys.readouterr().out
    assert 'n1["Issue #35;38;"]' in output
    assert "n0 --> n1" in output
