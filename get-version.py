"""Get qpc's version from pyproject.toml."""

import sys
import tomllib
from pathlib import Path

major_minor_zero = False

try:
    major_minor_zero = sys.argv[1] == "--major-minor"
except IndexError:
    pass

toml_path = Path(__file__).absolute().parent / "pyproject.toml"
with toml_path.open("rb") as fp:
    data = tomllib.load(fp)

output_version = data["project"]["version"]

if major_minor_zero:
    version, _, _ = output_version.rpartition(".")
    output_version = f"{version}.0"

print(output_version)
