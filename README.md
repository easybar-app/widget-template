# EasyBar Widget Template

A standalone starting point for an installable [EasyBar](https://easybar.dev) Lua widget. The
package can be installed directly from a checkout or release archive; publishing it in the
[official registry](https://github.com/easybar-app/widget-registry) is optional.

## Start a widget

Create a repository from this template, then replace the template identity before writing your
widget:

1. Replace `example-widget` and `example_widget` with your package and Lua node names.
2. Replace `Example Widget` and its description in `README.md` and `package.toml`.
3. Change `https://github.com/easybar-app/widget-template` to your repository URL.
4. Put your name and preferred license in `LICENSE` and `package.toml`.
5. Adapt `widget.lua` and `tests/test.lua` together.

Package names use lowercase letters, digits, and hyphens. Keep `package.toml` at the repository
root so both local installs and release archives have the layout EasyBar expects.

The starter widget deliberately keeps state in memory and uses only the core EasyBar API. Add
package dependencies under `[dependencies]` in `package.toml`; import an exported Lua module with
`local module = require("module")`. Put images and other runtime files under `assets/` and resolve
them with `easybar.asset("assets/file.svg")`. The package builder includes declared Lua files and
the complete `assets/` directory in release archives.

## Develop locally

The checks require Lua 5.5 and Python 3.11 or newer. StyLua is optional unless you run the format
targets.

```sh
make check
make lint-lua
make package
```

Install the checkout without publishing anything:

```sh
make install
```

That runs `easybar widgets install . --no-registry`. If your widget declares dependencies that
should be resolved from a registry, use `easybar widgets install .` instead. Reload EasyBar after
installing:

```sh
easybar config reload
```

Editor diagnostics use EasyBar's generated API definition at
`~/.local/share/easybar/easybar_api.lua`. Open this repository as the Lua workspace so
`.luarc.json` is applied.

The included regression test supplies a small fake EasyBar API, loads `widget.lua` in an isolated
environment, and invokes subscribed events directly. Extend that fake alongside the widget when
you use more EasyBar APIs, and assert user-visible state changes rather than internal helper
details.

`make package` writes a deterministic archive and checksum to `dist/`. Inspecting that archive
before the first release is a useful way to catch missing entrypoints, exports, assets, or README
files.

## Release

Bump the package version, review it, and commit it:

```sh
make bump LEVEL=patch
git add package.toml
git commit -m "chore: prepare 0.1.1"
git push origin main
```

Then create the package tag:

```sh
make release
```

`make release` requires a clean `main` branch synchronized with `origin/main`. It runs all checks
and pushes an annotated `<package>-v<version>` tag. The release workflow builds a deterministic
archive with `package.toml` at its root, publishes the archive and checksum to GitHub Releases,
and prints ready-to-copy registry metadata in the workflow summary.

## Publish in the registry

A registry entry makes the widget discoverable through `easybar widgets search` and installable by
name. It is not required for direct installation. After the first release, contribute
`packages/<package>.toml` to the
[widget registry](https://github.com/easybar-app/widget-registry) using the archive URL and SHA-256
from the release workflow.

The complete manifest and contribution guidance lives in the
[EasyBar documentation](https://easybar.dev/lua/guides/contributing-widget/).

## Make this repository a GitHub template

After pushing this repository, open **Settings → General**, enable **Template repository**, and use
**Use this template** to create new widget repositories.
