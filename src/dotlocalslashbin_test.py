#!/usr/bin/env python3
# src/dotlocalslashbin.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
"""Tests for src/dotlocalslashbin.py."""

import unittest
from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory

EXAMPLE_1 = Path("examples/1.toml").absolute()


class TestReadme(unittest.TestCase):
    """Tests based on README.md."""

    def test_fixture(self) -> None:
        """Parse the example from README.md and execute it."""
        marker = "```"
        lines = Path("README.md").read_text().splitlines()
        start = lines.index(marker) + 1
        stop = lines.index(marker, start)
        fixture = "\n".join(lines[start:stop])
        with TemporaryDirectory() as tmpdirname:
            Path(tmpdirname).joinpath("bin.toml").write_text(fixture)
            completed = run(
                [executable, Path("src/dotlocalslashbin.py").absolute(), "--output=."],
                cwd=tmpdirname,
                check=False,
                capture_output=True,
            )
            self.assertEqual(0, completed.returncode)


class TestCache(unittest.TestCase):
    """Test behaviour of the cache."""

    def _execute(self, extra: list[str]) -> int:
        with TemporaryDirectory() as cache, TemporaryDirectory() as output:
            Path(cache).joinpath("was_not_cleared").touch()
            run(
                [
                    executable,
                    Path("src/dotlocalslashbin.py").absolute(),
                    "--input=" + str(EXAMPLE_1),
                    f"--output={output}",
                    f"--cache={cache}",
                    *extra,
                ],
                check=True,
                capture_output=True,
            )
            return sum(1 for _ in Path(cache).iterdir())

    def test_example_without_clear(self) -> None:
        """Check that the cache is not cleared by default."""
        count = self._execute([])
        self.assertEqual(2, count)

    def test_example_with_clear(self) -> None:
        """Check that the cache is cleared."""
        count = self._execute(["--clear"])
        self.assertEqual(1, count)

    def test_example_with_no_clear(self) -> None:
        """Check that the cache is not cleared."""
        count = self._execute(["--no-clear"])
        self.assertEqual(2, count)


class TestInputs(unittest.TestCase):
    """Test behaviour of the the CLI with multiple inputs."""

    def _execute(self, inputs: list[str]) -> int:
        with TemporaryDirectory() as cache, TemporaryDirectory() as output:
            run(
                [
                    executable,
                    Path("src/dotlocalslashbin.py").absolute(),
                    f"--output={output}",
                    f"--cache={cache}",
                    *inputs,
                ],
                check=True,
                capture_output=True,
            )
            return sum(1 for _ in Path(output).iterdir())

    def test_one(self) -> None:
        """Check one input results in one output."""
        count = self._execute(
            [
                "--input=" + str(EXAMPLE_1),
            ],
        )
        self.assertEqual(1, count)


if __name__ == "__main__":
    unittest.main()
