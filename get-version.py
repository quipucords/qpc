"""Get qpc's version from pyproject.toml."""

import tomllib
from pathlib import Path

toml_path = Path(__file__).absolute().parent / "pyproject.toml"
with toml_path.open("rb") as fp:
    data = tomllib.load(fp)

print(data["project"]["version"])
