# EasyBar Widget Template

A standalone starting point for an installable Lua widget for EasyBar and EasyBar Native. Widgets
created from this template can be installed directly or published through the official registry.

## Features

- Minimal stateful Lua widget and focused regression test
- Package manifest, editor configuration, formatting, and validation
- Deterministic release archive and checksum generation
- Local installation and GitHub release workflows
- Optional publication through the EasyBar Widget Registry

## Requirements

- Lua 5.5
- Python 3.11 or newer
- EasyBar or EasyBar Native for local installation
- StyLua for formatting Lua source

## Create a widget

Create a repository from this template, then:

1. Replace `example-widget`, `example_widget`, and `Example Widget` with your package identity.
2. Update `package.toml`, the repository URL, this README, and the license.
3. Implement the widget in `widget.lua` and update `tests/test.lua` with its behavior.
4. Add runtime images or files below `assets/` and resolve them with `easybar.asset(...)`.
5. Run the complete checks and inspect the release archive.

```sh
make check
make package
```

Install the checkout into EasyBar with:

```sh
make install
easybar config reload
```

To test with EasyBar Native instead, install the checkout directly:

```sh
easybar-native widgets install . --no-registry
easybar-native config reload
```

## Documentation

- [Create and contribute packages](https://easybar.dev/widget-store/create-and-contribute/)
- [First Lua widget](https://easybar.dev/lua/guides/first-widget/)
- [Lua API reference](https://easybar.dev/lua/reference/)
- [Widget Store](https://easybar.dev/widget-store/overview/)

## License

The template is licensed under the [MIT License](./LICENSE). Replace the license when creating a
widget if you choose different terms.
