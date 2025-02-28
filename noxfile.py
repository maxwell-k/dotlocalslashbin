"""Reusable nox sessions for a single file project."""

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


@nox.session(python=PRIMARY, venv_backend="none")
def github_output(session: nox.Session) -> None:
    """Display outputs for CI integration."""
    scripts = set(Path("src").glob("*.py")) - set(Path("src").glob("*_test.py"))
    if len(scripts) > 1:
        session.error("More than one script found in src/")
    version = session.run(PYTHON, scripts.pop(), "--version", silent=True)
    print("version=" + cast(str, version).strip())  # version= adds quotes


@nox.session(python=PRIMARY)
def distributions(session: nox.Session) -> None:
    """Produce a source and binary distribution."""
    rmtree(DIST, ignore_errors=True)
    session.install("reproducibly")
    session.run("reproducibly", ".", DIST)
    sdist = next(DIST.iterdir())
    session.run("reproducibly", sdist, DIST)


@nox.session(python=PRIMARY, venv_backend="none")
def check(session: nox.Session) -> None:
    """Check the built distributions with twine."""
    session.run(_BIN / "twine", "check", "--strict", *DIST.glob("*.*"))


@nox.session(python=PRIMARY, venv_backend="none")
def static(session: nox.Session) -> None:
    """Run static analysis: usort, black and flake8.

    Use the tools that were previously installed into .venv so that:

    (1) the implementation or library stubs are available to type checkers
    (2) no time is spent installing a second time
    (3) versioning can be handled once

    """
    session.run(_BIN / "reuse", "lint")
    session.run(_BIN / "usort", "check", "src", "noxfile.py")
    session.run(_BIN / "black", "--check", ".")
    session.run(_BIN / "ruff", "check", ".")
    session.run(_BIN / "codespell")
    session.run(_BIN / "mypy", ".")
    session.run(
        _BIN / "yamllint",
        "--strict",
        "--config-file=.yamllint-config-file",
        ".github",
    )
    session.run(
        "npm",
        "exec",
        "pyright@1.1.396",
        "--yes",
        "--",
        f"--pythonpath={PYTHON}",
    )


@nox.session(python=PRIMARY, venv_backend="none")
def test(session: nox.Session) -> None:
    """Run test suite."""
    if sum(1 for _ in Path("src").glob("*_test.py")):
        session.run(PYTHON, "-m", "pytest", external=True)
    else:
        session.skip("No test files in repository")


# noxfile.py / https://github.com/maxwell-k/dotlocalslashbin/blob/main/noxfile.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
