from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fileops-core")
except PackageNotFoundError:
    # Package is being imported from a source checkout without an editable
    # install (e.g. a fresh clone before `pip install -e .`). Falling back
    # keeps `import fileops` usable for tooling like Sphinx or IDE indexing.
    __version__ = "0.0.0+unknown"
