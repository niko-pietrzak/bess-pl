from typer.testing import CliRunner

from bess.cli import app


def test_help_lists_commands():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "run" in result.output
