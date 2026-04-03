from click.testing import CliRunner

from lime_ai.app.agents.execute import execute


def test_execute_headless_missing_file_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(execute, ["does_not_exist.mgx", "--headless"])
    # missing file should cause silent non-zero exit in headless
    assert result.exit_code == 1
