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

    if spec_version != project["version"]:
        print(
            f"Versions '{project['version']}' in pyproject.toml and "
            f"'{spec_version}' in qpc.spec are inconsistent.",
            file=sys.stderr,
        )
        sys.exit(1)
