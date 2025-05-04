__all__ = ["__version__"]


def _pyproject_version() -> str:
    import re
    from pathlib import Path

    file: Path = Path(__file__).parents[1].joinpath("pyproject.toml")
    for line in file.open():
        m = re.match(r'^version = "(.+)"', line)
        if m:
            return m.group(1)

    raise RuntimeError("A version was not found in pyproject.toml")


__version__ = _pyproject_version()
