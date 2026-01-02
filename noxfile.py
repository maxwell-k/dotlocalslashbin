#!/usr/bin/env -S uv run
"""Reusable nox sessions for a single file project."""
# /// script
# dependencies = ["nox"]
# requires-python = ">=3.11"
# ///

from pathlib import Path
from shutil import rmtree

import nox
from nox.sessions import Session

nox.options.default_venv_backend = "uv"

VENV = ".venv"
PYTHON = Path().absolute() / VENV / "bin" / "python"
DIST = Path("dist")


@nox.session(venv_backend="none")
def dev(session: Session) -> None:
    """Set up a development environment (virtual environment)."""
    metadata = nox.project.load_toml("pyproject.toml")
    requires_python = metadata["project"]["requires-python"]
    session.run("uv", "venv", "--clear", "--python", requires_python, VENV)
    env = {"VIRTUAL_ENV": VENV}
    session.run("uv", "pip", "install", "--editable", ".[test]", env=env)


@nox.session()
def distributions(session: Session) -> None:
    """Produce a source and binary distribution."""
    rmtree(DIST, ignore_errors=True)
    session.install("reproducibly")
    session.run("reproducibly", ".", DIST)
    sdist = next(DIST.iterdir())
    session.run("reproducibly", sdist, DIST)


@nox.session()
def check(session: Session) -> None:
    """Check the built distributions with twine."""
    session.install("twine")
    session.run("twine", "check", "--strict", *DIST.glob("*.*"))


@nox.session(venv_backend="none", requires=["dev"])
def static(session: Session) -> None:
    """Run static analysis tools."""
    session.run(
        "npm",
        "exec",
        "pyright@1.1.407",
        "--yes",
        "--",
        f"--pythonpath={PYTHON}",
    )

    def run(cmd: str) -> None:
        session.run(PYTHON, "-m", *cmd.split())

    run("reuse lint")
    run("usort check .")
    run("black --check .")
    run("ruff check .")
    run("codespell_lib")
    run("mypy .")
    run("yamllint --strict .github")


@nox.session(venv_backend="none", requires=["dev"])
def test(session: Session) -> None:
    """Run test suite."""
    if sum(1 for _ in Path("src").glob("*_test.py")):
        session.run(PYTHON, "-m", "pytest", external=True)
    else:
        session.skip("No test files in repository")


if __name__ == "__main__":
    nox.main()


# noxfile.py / https://github.com/maxwell-k/dotlocalslashbin/blob/main/noxfile.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
