import json
import os
import sys

import pytest

from obsidian_vault_graph.cli import main


@pytest.mark.parametrize("flags,expected", [([], ["wiki"]), (["-c", "custom"], ["custom"]), (["-c", "a", "-c", "b"], ["a", "b"])])
def test_qmd_collection_flags_replace_default(tmp_path, monkeypatch, flags, expected):
    executable = tmp_path / "qmd"
    captured = tmp_path / "args.json"
    executable.write_text(
        f"#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\n"
        f"Path({str(captured)!r}).write_text(json.dumps(sys.argv[1:]))\nprint('[]')\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    main(["--vault", str(tmp_path), "qmd-topic", "query", *flags])
    args = json.loads(captured.read_text())
    assert [args[i + 1] for i, value in enumerate(args) if value == "-c"] == expected
