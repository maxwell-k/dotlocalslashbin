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

    uv tool run git+https://github.com/maxwell-k/dotlocalslashbin --version

## Example

For example to download `tofu` to the current working directory, first save the
following as `tofu.toml` then run the command below.

```
[tofu]
url = "https://github.com/opentofu/opentofu/releases/download/v1.10.3/tofu_1.10.3_linux_amd64.zip"
expected = "acf330602ec6ae29ba68dd5d8eb1f645811ae9809231ecdccd4774b21d5c79bc"
version = "version"
ignore = ["LICENSE", "README.md", "CHANGELOG.md"]
```

Command:

    uv tool run dotlocalslashbin --output=. tofu.toml

Further examples are available in files like `linux-amd64.toml` and
`github.toml` in the `bin` directory of
[maxwell-k/dotfiles](https://github.com/maxwell-k/dotfiles/).

## See also

<https://github.com/buildinspace/peru>

<!--
README.md
SPDX-FileCopyrightText: 2024 Keith Maxwell <keith.maxwell@gmail.com>
SPDX-License-Identifier: CC0-1.0
-->
<!-- vim: set filetype=markdown.htmlCommentNoSpell  : -->
