from pathlib import Path
from shutil import rmtree

import nox

PRIMARY = "3.11"
VIRTUAL_ENVIRONMENT = ".venv"
CWD = Path(".").absolute()
PYTHON = CWD / VIRTUAL_ENVIRONMENT / "bin" / "python"
SCRIPT = "src/dotlocalslashbin.py"
DIST = Path("dist")


@nox.session(python=False)
def dev(session) -> None:
    """Set up a development environment (virtual environment)"""
    rmtree(VIRTUAL_ENVIRONMENT, ignore_errors=True)
    session.run(f"python{PRIMARY}", "-m", "venv", "--upgrade-deps", VIRTUAL_ENVIRONMENT)
    session.run(PYTHON, "-m", "pip", "install", "--editable", ".[test]")


@nox.session(python=PRIMARY)
def reuse(session) -> None:
    """Run reuse lint outside of CI"""
    session.install("reuse")
    session.run("python", "-m", "reuse", "lint")


@nox.session(python=PRIMARY)
def github_output(session) -> None:
    """Display outputs for CI integration"""
    version = session.run("python", SCRIPT, "--version", silent=True).strip()
    print(f"version={version}")  # version= adds quotes


@nox.session(python=PRIMARY)
def distributions(session) -> None:
    """Produce a source and binary distribution"""
    rmtree(DIST, ignore_errors=True)
    session.install("reproducibly")
    session.run("reproducibly", ".", DIST)
    sdist = next(DIST.iterdir())
    session.run("reproducibly", sdist, DIST)


@nox.session(python=PRIMARY)
def check(session) -> None:
    """Check the built distributions with twine"""
    session.install("twine")
    session.run("twine", "check", "--strict", *DIST.glob("*.*"))


@nox.session(python=PRIMARY)
def static(session) -> None:
    """Run static analysis: usort, black and flake8"""
    session.install("usort")
    session.run("usort", "check", "src", "noxfile.py")

    session.install("black")
    session.run("black", "--check", ".")

    session.install("flake8")
    session.run("flake8")

    session.install("codespell")
    session.run("codespell")


# noxfile.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
