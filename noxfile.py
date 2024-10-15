"""Reusable nox sessions for a single file project with no tests."""

from pathlib import Path
from shutil import rmtree
from typing import cast

import nox

PRIMARY = "3.13"
VIRTUAL_ENVIRONMENT = ".venv"
_CWD = Path().absolute()
_BIN = _CWD / VIRTUAL_ENVIRONMENT / "bin"
PYTHON = _BIN / "python"
DIST = Path("dist")


@nox.session(python=False)
def dev(session: nox.Session) -> None:
    """Set up a development environment (virtual environment)."""
    rmtree(VIRTUAL_ENVIRONMENT, ignore_errors=True)
    session.run(f"python{PRIMARY}", "-m", "venv", "--upgrade-deps", VIRTUAL_ENVIRONMENT)
    session.run(PYTHON, "-m", "pip", "install", "--editable", ".[test]")


@nox.session(python=PRIMARY)
def reuse(session: nox.Session) -> None:
    """Run reuse lint outside of CI."""
    session.install("reuse")
    session.run("python", "-m", "reuse", "lint")


@nox.session(python=PRIMARY)
def github_output(session: nox.Session) -> None:
    """Display outputs for CI integration."""
    if len(scripts := list(Path("src").glob("*.py"))) > 1:
        session.error("More than one script found in src/")
    version = session.run("python", scripts[0], "--version", silent=True)
    print("version=" + cast(str, version).strip())  # version= adds quotes


@nox.session(python=PRIMARY)
def distributions(session: nox.Session) -> None:
    """Produce a source and binary distribution."""
    rmtree(DIST, ignore_errors=True)
    session.install("reproducibly")
    session.run("reproducibly", ".", DIST)
    sdist = next(DIST.iterdir())
    session.run("reproducibly", sdist, DIST)


@nox.session(python=PRIMARY)
def check(session: nox.Session) -> None:
    """Check the built distributions with twine."""
    session.install("twine")
    session.run("twine", "check", "--strict", *DIST.glob("*.*"))


@nox.session(python=PRIMARY)
def static(session: nox.Session) -> None:
    """Run static analysis: usort, black and flake8.

    Use the tools that were previously installed into .venv so that:

    (1) the implementation or library stubs are available to type checkers
    (2) no time is spent installing a second time
    (3) versioning can be handled once

    """
    session.run(_BIN / "usort", "check", "src", "noxfile.py", external=True)
    session.run(_BIN / "black", "--check", ".", external=True)
    session.run(_BIN / "ruff", "check", ".", external=True)
    session.run(_BIN / "codespell", external=True)
    session.run(_BIN / "mypy", ".", external=True)
    session.run(
        "npm",
        "exec",
        "pyright@1.1.383",
        "--yes",
        "--",
        f"--pythonpath={PYTHON}",
        external=True,
    )


# noxfile.py / https://github.com/maxwell-k/dotlocalslashbin/blob/main/noxfile.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
