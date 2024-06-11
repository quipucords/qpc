"""QPC pyproject toml and spec file verification."""

import re
import sys
from pathlib import Path
from tomllib import load

spec_path = Path(__file__).absolute().parent / "qpc.spec"
match_version = re.search(r"Version:\s+(\d+\.\d+\.\d+)", spec_path.read_text())
if not match_version:
    print("Unable to parse version on qpc.spec", file=sys.stderr)
    sys.exit(1)
spec_version = match_version.groups()[0]

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

    if spec_version != project["version"] or spec_version != tool_poetry["version"]:
        print(
            "Versions {v1} (project) and {v2} (tool.poetry) in pyproject.toml, and "
            "{v3} in qpc.spec are inconsistent.".format(
                v1=project["version"], v2=tool_poetry["version"], v3=spec_version
            ),
            file=sys.stderr,
        )
        sys.exit(1)
