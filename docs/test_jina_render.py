"""Tests for jinja-render.py standalone script."""

import importlib.util
import os
import random
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest

sample_jinja_template = "hello, {{ NAME }}"


@pytest.fixture(scope="module")
def jinja_render():
    """
    Import the jinja-render script as a module.

    This is necessary because jinja-render.py is a standalone script
    that does not live in a regular Python package.
    """
    module_name = "jinja_render"
    file_path = Path(__file__).parent / "jinja-render.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_env_vars(jinja_render, mocker):
    """Test getting only env vars that match the given pattern."""
    mocker.patch.dict(
        os.environ,
        {
            "unrelated": "zero",
            "QPC_THING": "one",
            "QPC_thang": "two",
            "NOT_QPC_OTHER": "three",
        },
        clear=True,
    )
    expected = {"QPC_THING": "one", "QPC_thang": "two"}
    allow_pattern = "^QPC_.*"
    actual = jinja_render.get_env_vars(allow_pattern)
    assert actual == expected


def test_read_stdin_write_stdout(jinja_render, mocker, capsys):
    """Test reading the Jinja template from stdin and writing output to stdout."""
    fake_name = str(random.random())
    expected_stdout = f"hello, {fake_name}"

    fake_env_vars = {"NAME": fake_name}
    fake_sys_argv = ["script.py", "-e", ".*"]
    fake_stdin = StringIO(sample_jinja_template)

    mocker.patch.dict(os.environ, fake_env_vars, clear=True)
    mocker.patch.object(sys, "argv", fake_sys_argv)
    mocker.patch.object(sys, "stdin", fake_stdin)

    jinja_render.main()
    actual_stdout = capsys.readouterr().out
    assert actual_stdout == expected_stdout


@pytest.fixture
def template_path():
    """Temp file containing a Jija template."""
    tmp_file = tempfile.NamedTemporaryFile()
    tmp_file.write(sample_jinja_template.encode())
    tmp_file.seek(0)
    yield tmp_file.name
    tmp_file.close()


def test_read_file_write_file(jinja_render, template_path, mocker, capsys):
    """Test reading the Jinja template from file and writing output to file."""
    fake_name = str(random.random())
    expected_stdout = f"hello, {fake_name}"
    fake_env_vars = {"NAME": fake_name}
    with tempfile.TemporaryDirectory() as output_directory:
        output_path = Path(output_directory) / str(random.random())
        fake_sys_argv = [
            "script.py",
            "-e",
            ".*",
            "-t",
            template_path,
            "-o",
            str(output_path),
        ]
        mocker.patch.dict(os.environ, fake_env_vars, clear=True)
        mocker.patch.object(sys, "argv", fake_sys_argv)
        jinja_render.main()

        with output_path.open() as output_file:
            actual_output = output_file.read()

    assert actual_output == expected_stdout
