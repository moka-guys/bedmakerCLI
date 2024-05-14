from typer.testing import CliRunner
import bedmaker
import bedmaker.transcripts.cli as transcripts


def test_version():
    """Test the version command."""
    runner = CliRunner()
    result = runner.invoke(transcripts.app, ["version"])
    output = result.output.rstrip()
    assert output == bedmaker.__version__
