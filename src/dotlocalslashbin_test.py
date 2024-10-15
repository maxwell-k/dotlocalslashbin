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


if __name__ == "__main__":
    unittest.main()
