"""Public package for ghost dynamical mean-field theory."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gdmft")
except PackageNotFoundError:  # Source checkout without installation.
    __version__ = "0+unknown"

__all__ = ["__version__"]
