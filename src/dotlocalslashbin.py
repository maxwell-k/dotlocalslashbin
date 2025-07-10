#!/usr/bin/env python3
# src/dotlocalslashbin.py
# Copyright 2022 Keith Maxwell
# SPDX-License-Identifier: MPL-2.0
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Download and extract files to `~/.local/bin/`."""
import tarfile
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from dataclasses import dataclass
from enum import Enum
from hashlib import file_digest
from pathlib import Path
from shlex import split
from shutil import copy
from stat import S_IEXEC
from subprocess import run
from tomllib import load
from urllib.error import HTTPError
from urllib.request import urlopen
from zipfile import ZipFile


__version__ = "0.0.17"

_CACHE = Path("~/.cache/dotlocalslashbin/")
_HOME = str(Path("~").expanduser())
_INPUT = "bin.toml"
_OUTPUT = Path("~/.local/bin/")
_SHA512_LENGTH = 128


class _CustomNamespace(Namespace):
    output: Path
    input: list[Path]
    cache: Path


Action = Enum("Action", ["command", "copy", "symlink", "untar", "unzip"])


@dataclass(init=False)
class Item:
    """Class for an application."""

    name: str
    url: str
    target: Path
    action: Action
    downloaded: Path
    expected: str | None
    version: str
    prefix: str
    command: str | None
    ignore: set


def main() -> int:
    """Parse command line arguments and download each file."""
    args = _parse_args()

    if args.clear:
        for path in args.cache.expanduser().iterdir():
            path.unlink()

    data: dict[str, dict] = {}
    for i in args.input:
        with i.expanduser().open("rb") as file:
            data |= load(file)

    for name, record in data.items():
        item = Item()
        item.name = name
        item.url = record["url"]
        default = args.output.joinpath(name)
        item.target = Path(record.get("target", default)).expanduser()
        item.ignore = record.get("ignore", set())
        item.expected = record.get("expected", None)
        item.version = record.get("version", "")
        item.prefix = record.get("prefix", "")
        item.command = record.get("command", None)

        if "action" in record:
            item.action = getattr(Action, record["action"])
        else:
            item.action = _guess_action(item)

        if item.url.startswith("https://"):
            item.downloaded = args.cache.expanduser() / item.url.rsplit("/", 1)[1]
        else:
            item.downloaded = Path(item.url)
        try:
            _process(item)
        except HTTPError as e:
            print(f"Error {e.code} downloading {e.url}")
            return 1

        arg0 = str(item.target.absolute())
        prompt = "#" if item.version else "$"
        print(" ".join((prompt, arg0.replace(_HOME, "~"), item.version)))
        if item.version:
            run([arg0, item.version], check=True)
        print()

    return 0


def _process(item: Item) -> None:
    """Context manager to download and install a program."""
    if not item.downloaded.is_file() and item.url.startswith("https://"):
        _download(item)

    if item.expected:
        with item.downloaded.open("rb") as f:
            _digest = "sha512" if len(item.expected) == _SHA512_LENGTH else "sha256"
            digest = file_digest(f, _digest)

        if (actual := digest.hexdigest()) != item.expected:
            msg = f"Unexpected digest for {item.downloaded}: {actual=} {item.expected=}"
            raise RuntimeError(msg)

    item.target.parent.mkdir(parents=True, exist_ok=True)
    item.target.unlink(missing_ok=True)
    if item.action == Action.copy:
        copy(item.downloaded, item.target)
    elif item.action == Action.symlink:
        item.target.symlink_to(item.downloaded)
    elif item.action == Action.unzip:
        with ZipFile(item.downloaded, "r") as file:
            file.extract(item.target.name, path=item.target.parent)
    elif item.action == Action.untar:
        _untar(item)
    elif item.action == Action.command and item.command is not None:
        kwargs = {"target": item.target, "downloaded": item.downloaded}
        run(split(item.command.format(**kwargs)), check=True)

    if not item.target.is_symlink():
        item.target.chmod(item.target.stat().st_mode | S_IEXEC)


def _parse_args() -> _CustomNamespace:
    parser = ArgumentParser(
        prog=Path(__file__).name,
        epilog="¹ --input can be specified multiple times",
    )
    parser.add_argument("--version", action="version", version=__version__)
    help_ = f"TOML specification (default: {_INPUT})¹"
    parser.add_argument("--input", action="append", help=help_, type=Path)
    help_ = f"Target directory (default: {_OUTPUT})"
    parser.add_argument("--output", default=_OUTPUT, help=help_, type=Path)
    help_ = f"Cache directory (default: {_CACHE})"
    parser.add_argument("--cache", default=_CACHE, help=help_, type=Path)
    help_ = "Clear the cache directory first (default: --no-clear)"
    parser.add_argument("--clear", action=BooleanOptionalAction, help=help_)
    result = parser.parse_args(namespace=_CustomNamespace())
    if not result.input:
        result.input = [Path(_INPUT)]
    return result


def _download(item: Item) -> None:
    item.downloaded.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(item.url) as fp, item.downloaded.open("wb") as dp:
        size = int(fp.headers.get("Content-Length", -1))
        print(f"Downloading {item.name}…")
        written = dp.write(fp.read())

    if size >= 0 and written != size:
        msg = "Wrong content length"
        raise RuntimeError(msg)


def _untar(item: Item) -> None:
    with tarfile.open(item.downloaded, "r") as file:
        for member in file.getmembers():
            if member.path in item.ignore:
                continue
            member.path = member.path.removeprefix(item.prefix)
            try:
                file.extract(member, path=item.target.parent, filter="tar")
            except TypeError:  # before 3.11.4 e.g. Debian 12
                file.extract(member, path=item.target.parent)


def _guess_action(item: Item) -> Action:
    if item.url.endswith((".tar.gz", ".tar")):
        guess = Action.untar
    elif item.url.endswith(".zip"):
        guess = Action.unzip
    elif item.url.startswith("/"):
        guess = Action.symlink
    elif item.command:
        guess = Action.command
    else:
        guess = Action.copy
    return guess


if __name__ == "__main__":
    raise SystemExit(main())
