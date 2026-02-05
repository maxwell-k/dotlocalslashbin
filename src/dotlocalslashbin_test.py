#!/usr/bin/env python3
# src/dotlocalslashbin.py
# Copyright 2024 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
"""Tests for src/dotlocalslashbin.py."""

import contextlib
import os
import unittest
import zipfile
from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory

from dotlocalslashbin import main

EXAMPLE_1 = Path("examples/1.toml").absolute()
EXAMPLE_2 = Path("examples/2.toml").absolute()


def silent(args: list[str]) -> None:
    """Call main with stdout redirected to devnull."""
    with Path(os.devnull).open("w") as f, contextlib.redirect_stdout(f):
        main(args)


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
        for i in EXAMPLE_1, EXAMPLE_2:
            count = self._execute(["--input=" + str(i)])
            self.assertEqual(1, count)

    def test_both(self) -> None:
        """Check that two input files together result in two outputs."""
        count = self._execute(["--input=" + str(i) for i in [EXAMPLE_1, EXAMPLE_2]])
        self.assertEqual(2, count)

    def test_zip_file(self) -> None:
        """Create a zip with one file."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            cache = Path(_cache)
            source = Path(_source)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.write(a, arcname=a.name)

            _input = source / "input.toml"
            _input.write_text('[a]\nurl = "https://example.com/a.zip"\n')

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_zip_file_with_prefix(self) -> None:
        """Create a zip with one file in a prefix."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            cache = Path(_cache)
            source = Path(_source)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.writestr("b/", "")
                _zip.write(a, arcname="b/" + a.name)

            _input = source / "input.toml"
            _input.write_text('[a]\nurl = "https://example.com/a.zip"\nprefix = "b/"\n')

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_zip_file_two_files(self) -> None:
        """Create a zip with one file name differently."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            source = Path(_source)
            cache = Path(_cache)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")
            b = source / "b"
            b.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.write(a, arcname=a.name)
                _zip.write(b, arcname=b.name)

            _input = source / "input.toml"
            _input.write_text('[a]\nurl = "https://example.com/a.zip"\n')

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")
            self.assertEqual(output.joinpath("b").read_text(), "hello world")

    def test_zip_file_with_prefix_no_trailing_slash(self) -> None:
        """Create a zip with one file in a prefix."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            cache = Path(_cache)
            source = Path(_source)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.write(a, arcname="b/" + a.name)

            _input = source / "input.toml"
            _input.write_text('[a]\nurl = "https://example.com/a.zip"\nprefix = "b"\n')

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")

    def test_zip_file_second_file_outside_prefix(self) -> None:
        """Create a zip with one file in a prefix."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            cache = Path(_cache)
            source = Path(_source)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")
            c = source / "c"
            c.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.write(a, arcname="b/" + a.name)
                _zip.write(c, arcname=c.name)

            _input = source / "input.toml"
            _input.write_text('[a]\nurl = "https://example.com/a.zip"\nprefix = "b"\n')

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")
            self.assertEqual(sum(1 for _ in output.iterdir()), 1)

    def test_zip_file_ignore(self) -> None:
        """Teset the ignore feature."""
        with (
            TemporaryDirectory(prefix="source_") as _source,
            TemporaryDirectory(prefix="cache_") as _cache,
            TemporaryDirectory(prefix="output_") as _output,
        ):
            source = Path(_source)
            cache = Path(_cache)
            output = Path(_output)

            a = source / "a"
            a.write_text("hello world")
            b = source / "b"
            b.write_text("hello world")

            zip_path = cache / "a.zip"
            with zipfile.ZipFile(zip_path, "w") as _zip:
                _zip.write(a, arcname=a.name)
                _zip.write(b, arcname=b.name)

            _input = source / "input.toml"
            _input.write_text(
                '[a]\nurl = "https://example.com/a.zip"\nignore = ["b"]\n',
            )

            args = [f"--output={output}", f"--cache={cache}", f"--input={_input}"]
            silent(args)

            self.assertEqual(output.joinpath("a").read_text(), "hello world")
            self.assertFalse(output.joinpath("b").exists(), "b should not exist")


if __name__ == "__main__":
    unittest.main()
