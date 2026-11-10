import importlib.util
from pathlib import Path

from click.testing import CliRunner


def load_cli():
    spec = importlib.util.spec_from_file_location("the_moon", Path(__file__).parents[2] / "the-moon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.cli


def test_studio_command_is_registered():
    res = CliRunner().invoke(load_cli(), ["studio", "--help"])
    assert res.exit_code == 0 and "--port" in res.output and "--no-open" in res.output
