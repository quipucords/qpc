"""QPC pyproject toml file verification."""

import sys
from pathlib import Path
from tomllib import load

toml_path = Path(__file__).absolute().parent / "pyproject.toml"
with toml_path.open("rb") as toml_file:
    toml_data = load(toml_file)
    project = toml_data["project"]
    tool_poetry = toml_data["tool"]["poetry"]

    if project["name"] != tool_poetry["name"]:
        print(
            "Project name {n1} does not match tool.poetry name {n2}".format(
                n1=project["name"], n2=tool_poetry["name"]
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    if project["version"] != tool_poetry["version"]:
        print(
            "Project version {v1} does not match tool.poetry version {v2}".format(
                v1=project["version"], v2=tool_poetry["version"]
            ),
            file=sys.stderr,
        )
        sys.exit(1)
