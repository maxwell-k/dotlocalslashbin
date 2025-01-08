`dotlocalslashbin` → Download to `~/.local/bin/`

## Features

Uses a [TOML] configuration file, by default `bin.toml` and has no dependencies
beyond the Python standard library. Supports the following actions after
downloading the URL\* to a cache:

- extract to the output directory — from zip or tar files — or
- create a symbolic link in the output directory or
- run a command for example to correct the shebang line in a zipapp or
- copy the downloaded file

Guesses the correct action if none is specified. By default caches downloads to
`~/.cache/dotlocalslashbin/`.

Optionally can:

- run a command after download for example to correct a shebang line
- confirm a SHA256 or SHA512 hex-digest of the downloaded file
- invoke the target with an argument, for example `--version`
- strip a prefix while extracting
- ignore certain files while extracting
- clear the cache beforehand

\* if the URL is an absolute path on the local file system; it is not downloaded
to the cache.

[uv]: https://github.com/astral-sh/uv
[TOML]: https://en.wikipedia.org/wiki/TOML

## Installation

The recommended way to run `dotlocalslashbin` is with [uv].

Command to install the latest released `dotlocalslashbin` from PyPI:

    uv tool install dotlocalslashbin

Command to run latest development version of `dotlocalslashbin` directly from
GitHub:

    uv run https://raw.githubusercontent.com/maxwell-k/dotlocalslashbin/refs/heads/main/src/dotlocalslashbin.py --version

## Examples

For example to download `yq` to the current working directory, first save the
following as `yq.toml`, then install with uv (above) and then run the command
below:

```
[yq]
expected = "cfbbb9ba72c9402ef4ab9d8f843439693dfb380927921740e51706d90869c7e1"
url = "https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64"
version = "--version"
```

Command:

    dotlocalslashbin --input=yq.toml --output=.

Further examples are available in
[`bin.toml` in maxwell-k/dotfiles](https://github.com/maxwell-k/dotfiles/blob/main/bin.toml).

## See also

<https://github.com/buildinspace/peru>

<!--
README.md
SPDX-FileCopyrightText: 2024 Keith Maxwell <keith.maxwell@gmail.com>
SPDX-License-Identifier: CC0-1.0
-->
<!-- vim: set filetype=markdown.htmlCommentNoSpell  : -->
