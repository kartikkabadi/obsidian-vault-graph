import pytest

from obsidian_vault_graph.cli import main


def test_scope_cannot_escape_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (tmp_path / "outside.md").write_text("outside")
    with pytest.raises(SystemExit, match="Scope must be inside"):
        main(["--vault", str(vault), "--scope", "..", "status"])


def test_vault_must_be_a_directory(tmp_path):
    path = tmp_path / "file.md"
    path.write_text("not a directory")
    with pytest.raises(SystemExit, match="Vault is not a directory"):
        main(["--vault", str(path), "status"])


def test_missing_scope_is_reported(tmp_path):
    with pytest.raises(SystemExit, match="Scope is not a directory"):
        main(["--vault", str(tmp_path), "--scope", "missing", "status"])
