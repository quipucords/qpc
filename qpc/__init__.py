"""QPC Package Initialization."""
from importlib import metadata
from pathlib import Path
from tomllib import load

try:
    # Let's get the package version from poetry
    __package__version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # PackageNotFoundError may be raised if *not* called from
    # within a poetry environment, such as during execution of
    # `python setup.py install` in downstream builds.
    # As a failsafe, try to load the version defined for poetry
    # from the pyproject.toml.
    toml_path = Path(__file__).absolute().parent.parent / "pyproject.toml"
    with open(toml_path, "rb") as f:
        toml_data = load(f)
        __package__version__ = (
            # Expect a value at this exact location.
            # Yes, this will raise KeyError if absent.
            # We want to know ASAP if this breaks.
            toml_data["tool"]["poetry"]["version"]
        )

del load
del Path
del metadata
