#!/usr/bin/env python3
# src/dotlocalslashbin.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
"""Tests for src/dotlocalslashbin.py."""

import contextlib
import os
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from subprocess import run
from sys import executable
from tarfile import TarFile
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from dotlocalslashbin import main

EXAMPLE_1 = Path("examples/1.toml").absolute()
EXAMPLE_2 = Path("examples/2.toml").absolute()


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
            Path(tmpdirname).joinpath("example.toml").write_text(fixture)
            args = [
                executable,
                str(Path("src/dotlocalslashbin.py").absolute()),
                "--output=.",
                "example.toml",
            ]
            completed = run(args, cwd=tmpdirname, check=False, capture_output=True)

        msg = None
        if completed.stderr:
            decoded = completed.stderr.decode()
            msg = f"Return code incorrect.\n\nOutput to standard error:\n\n {decoded}"
        self.assertEqual(0, completed.returncode, msg=msg)


class TestCache(unittest.TestCase):
    """Test behaviour of the cache."""

    def _execute(self, extra: list[str]) -> int:
        with TemporaryDirectory() as cache, TemporaryDirectory() as output:
            Path(cache).joinpath("was_not_cleared").touch()
            run(
                [
                    executable,
                    Path("src/dotlocalslashbin.py").absolute(),
                    f"--output={output}",
                    f"--cache={cache}",
                    *extra,
                    str(EXAMPLE_1),
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
        for i in EXAMPLE_1, EXAMPLE_2:
            count = self._execute([str(i)])
            self.assertEqual(1, count)

    def test_both(self) -> None:
        """Check that two input files together result in two outputs."""
        count = self._execute([str(i) for i in [EXAMPLE_1, EXAMPLE_2]])
        self.assertEqual(2, count)


@contextmanager
def _directory(prefix: str) -> Iterator[Path]:
    """Create a temporary directory with a prefix."""
    with TemporaryDirectory(prefix=prefix) as directory:
        yield Path(directory)


@contextmanager
def call(toml: str, cache: Path) -> Iterator[Path]:
    """Wrap main yielding a temporary output directory."""
    with _directory("input_") as directory, _directory("output_") as output:
        _input = directory / "input.toml"
        _input.write_text(toml)
        args = [f"--output={output}", f"--cache={cache}", f"{_input}"]
        with Path(os.devnull).open("w") as f, contextlib.redirect_stdout(f):
            main(args)
        yield output


def _write_zip(
    target: Path,
    contents: list[Path],
    relative_to: Path | None = None,
) -> None:
    """Write contents to target.

    Assumes all files are at the root level, if relative_to is None.
    """
    with ZipFile(target, "w") as _zip:
        for i in contents:
            arcname = str(i.relative_to(relative_to)) if relative_to else i.name
            _zip.write(i, arcname=arcname)


class TestZip(unittest.TestCase):
    """Test the main function when input is a single zip file."""

    def test_basic(self) -> None:
        """Process a zip with one file."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")

            _write_zip(cache / "a.zip", [a])
            toml = '[a]\nurl = "https://example.com/a.zip"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_prefix(self) -> None:
        """Process a zip with one file in a prefix."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")

            zip_path = cache / "a.zip"
            with ZipFile(zip_path, "w") as _zip:
                _zip.writestr("b/", "")
                _zip.write(a, arcname="b/" + a.name)

            toml = '[a]\nurl = "https://example.com/a.zip"\nprefix = "b/"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_two_files(self) -> None:
        """Process a zip with two files."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")
            b = source / "b"
            b.write_text("hello world")

            _write_zip(cache / "a.zip", [a, b])
            toml = '[a]\nurl = "https://example.com/a.zip"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")
                self.assertEqual(output.joinpath("b").read_text(), "hello world")

    def test_prefix_no_trailing_slash(self) -> None:
        """Process a zip file with a prefix with no trailing slash."""
        with _directory("source_") as source, _directory("cache_") as cache:
            (b := source / "b").mkdir()
            a = b / "a"
            a.write_text("hello world")

            _write_zip(cache / "a.zip", [a], source)
            toml = '[a]\nurl = "https://example.com/a.zip"\nprefix = "b"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_file_outside_prefix(self) -> None:
        """Process a zip with a file outside the prefix."""
        with _directory("source_") as source, _directory("cache_") as cache:
            (b := source / "b").mkdir()
            a = b / "a"
            a.write_text("hello world")
            c = source / "c"
            c.write_text("hello world")

            _write_zip(cache / "a.zip", [a, c], source)
            toml = '[a]\nurl = "https://example.com/a.zip"\nprefix = "b"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")
                self.assertEqual(sum(1 for _ in output.iterdir()), 1)

    def test_ignore(self) -> None:
        """Process an input that uses the ignore feature."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")
            b = source / "b"
            b.write_text("hello world")

            _write_zip(cache / "a.zip", [a, b])
            toml = '[a]\nurl = "https://example.com/a.zip"\nignore = ["b"]\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")
                self.assertEqual(sum(1 for _ in output.iterdir()), 1)

    def test_prefix_and_ignore(self) -> None:
        """Process an input that uses the prefix and ignore features together."""
        with _directory("source_") as source, _directory("cache_") as cache:
            (b := source / "b").mkdir()
            a = b / "a"
            a.write_text("hello world")
            c = b / "ignored"
            c.write_text("hello world")

            _write_zip(cache / "b.zip", [a, c], source)
            toml = '[a]\nurl = "https://example.com/b.zip"\n'
            toml += 'ignore = ["ignored"]\nprefix = "b/"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")
                self.assertEqual(sum(1 for _ in output.iterdir()), 1)

    def test_name_is_not_a_file(self) -> None:
        """Process an input with a name that doesn't match a file."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")

            _write_zip(cache / "a.zip", [a])
            toml = '[b]\nurl = "https://example.com/a.zip"\n'

            with call(toml, cache) as output:
                self.assertEqual(output.joinpath("a").read_text(), "hello world")
                self.assertEqual(sum(1 for _ in output.iterdir()), 1)


class TestTar(unittest.TestCase):
    """Test the main function when input is a single tar.gz file."""

    def test_basic(self) -> None:
        """Process a tar with one file in at an absolute path."""
        with _directory("source_") as source, _directory("cache_") as cache:
            a = source / "a"
            a.write_text("hello world")

            tar_path = cache / "a.tar.gz"
            with TarFile.open(tar_path, "w:gz") as tar:
                tar.add(a)

            toml = '[a]\nurl = "https://example.com/a.tar.gz"\n'

            with call(toml, cache) as output:
                self.assertEqual(sum(1 for _ in output.iterdir()), 1)


if __name__ == "__main__":
    unittest.main()
