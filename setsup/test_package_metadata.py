import re

import fileops

_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+")


def test_version_is_exposed_and_semver_formatted() -> None:
    assert _SEMVER_PATTERN.match(fileops.__version__)


def test_version_matches_installed_distribution_metadata() -> None:
    from importlib.metadata import version

    assert fileops.__version__ == version("fileops-core")
