"""QPC Package Initialization."""
from importlib import metadata

# Let's get the package version from poetry
__package__version__ = metadata.version(__package__)
del metadata
