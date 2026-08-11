# EasyBar Widget Agent Guide

## Scope and intent

These instructions apply to the entire repository. This repository starts as a generic template,
but a repository created from it should describe and ship one standalone EasyBar widget. Keep the
package self-contained, releaseable, and understandable without requiring the EasyBar source
checkout.

Preserve user changes already present in the worktree. Do not commit, push, create tags, publish a
release, or submit registry metadata unless the user explicitly requests that action.

## Creating a widget from the template

Before implementing widget behavior, replace the template identity consistently:

1. Choose a lowercase, hyphen-separated package name such as `weather-status`.
2. Replace `example-widget` in `package.toml`, commands, and documentation.
3. Replace the Lua node name `example_widget` in `widget.lua` and `tests/test.lua`. Node names
   should use underscores and should be specific enough to avoid collisions.
4. Update the package description, README title and behavior, repository URL, author information,
   and license. Keep a new package at version `0.1.0`.
5. Adapt the widget and its regression test together. Remove example behavior that no longer
   represents the real widget.

Search the entire repository for the old identifiers after renaming them. A new widget is not
ready while `example-widget`, `example_widget`, `Example Widget`, or the template repository URL
remain unintentionally.

## Package contract

`package.toml` is the source of truth for packaging and compatibility:

- Keep `manifest_version = 2`, `kind = "widget"`, and `package.toml` at the repository root.
- Keep package names lowercase and hyphen-separated. Follow semantic versioning.
- Set `entrypoint` to the actual widget entrypoint and `readme` to the package README.
- Set `minimum_easybar_kit_version` to the oldest EasyBarKit version whose APIs the widget actually uses.
- Every non-test Lua file must be the entrypoint or a module declared under `[exports]`.
- Declare other EasyBar packages under `[dependencies]` with an exact or caret semantic-version
  constraint. The package name and the module passed to `require(...)` are not necessarily the
  same; require the module name exported by the dependency.
- Declare external commands, environment variables, settings, native-inbox use, and other
  manifest capabilities when the widget needs them. Follow the current EasyBar package
  documentation and existing official packages for supported manifest tables.
- Store runtime images and other files below `assets/`. Resolve them from Lua with
  `easybar.asset("assets/name.svg")`; do not embed absolute or machine-specific paths.
- Never commit generated archives, checksum files, or the `dist/` directory.

Release archives must contain `package.toml` at their root. The packaging script includes the
manifest, README, license, declared Lua files, and files below `assets/`; tests and development
tooling are intentionally excluded.

## Lua implementation

- Target Lua 5.5. Use the widget-scoped `easybar` global supplied by EasyBar; do not import it or
  create additional globals.
- Prefer local state and local functions. Give every named function an adjacent `---` description
  that explains its purpose. Add LuaLS `---@param`, `---@return`, aliases, or classes when they
  clarify public modules or non-obvious data boundaries; do not annotate obvious details merely
  to increase comment volume.
- Keep rendering derived from explicit widget state. Event callbacks should update state and then
  render, rather than scattering unrelated visual mutations across callbacks.
- Use EasyBar's asynchronous command and timer APIs for slow work. Avoid blocking the runtime,
  overlapping refreshes, and callbacks that can apply stale results after cancellation or a newer
  request.
- Pass external command arguments as an argument list. Never construct a shell command by
  concatenating settings, API data, filenames, or other untrusted values.
- Bound command time and output where the API supports it, handle non-zero and cancellation exit
  codes, and expose actionable failures without leaking credentials or tokens.
- Validate decoded JSON and external command output before indexing fields. Preserve the last
  useful rendered state when a temporary refresh fails where that behavior makes sense.
- Use `easybar.storage` for persistent user choices and validate stored values before use. Keep
  storage namespaces and keys stable after release unless a migration is provided.
- Use theme references and template-style SVGs where practical so the widget works with different
  appearances. Do not assume one bar color or background.
- Consult `~/.local/share/easybar/easybar_api.lua` and the current documentation at
  <https://easybar.dev> instead of inventing EasyBar APIs.

## Tests

`tests/test.lua` is a deterministic regression test, not a live EasyBar integration test. Its fake
API should include only the behavior needed by the widget.

- Extend the fake EasyBar API whenever production code starts using another API surface.
- Load `widget.lua` in the isolated environment used by the template; do not make tests depend on
  globals from the developer's machine.
- Invoke subscribed callbacks directly and assert user-visible properties, published data,
  commands, or state transitions.
- Cover the initial render and every user action. Add focused cases for parsing failures,
  cancellation, overlapping asynchronous work, persisted settings, and error recovery when those
  concerns exist in the widget.
- Keep tests offline and deterministic. Do not call real network services, mutate the user's
  EasyBar data, run destructive commands, or require authentication.
- Update tests in the same change as behavior. A test should fail for the regression it protects.

## README expectations

Replace the template setup instructions with documentation for the finished widget. The package
README should state:

- what appears in the bar and what each click, menu action, or inbox action does;
- required external tools, macOS permissions, authentication, and supported service versions;
- all settings, their defaults, accepted values, and whether changes require a reload;
- dependencies and any required setup outside EasyBar;
- local installation and normal package installation instructions;
- known safety implications for actions that modify external state.

Use example values only. Never add credentials, private URLs, local usernames, absolute paths, or
machine-specific output.

## Validation workflow

Use the repository targets rather than reimplementing their checks:

```sh
make fmt
make check
make lint-lua
make package
```

- `make fmt` formats Lua, Markdown, YAML, JSON, and TOML files. Use a target such as `make fmt-lua`
  or `make fmt-md` when only one format needs updating.
- `make check` validates the manifest, parses every Lua file with Lua 5.5, and runs the regression
  test.
- `make lint-lua` verifies StyLua formatting. Run `make fmt-lua` before it when Lua changed.
- `make package` builds the deterministic archive and SHA-256 in `dist/`. Run it when the manifest,
  declared files, assets, or packaging behavior changes, and inspect the archive before the first
  release.
- Run `git diff --check` before handing work back.

Lua 5.5 and Python 3.11 or newer are required. StyLua is required for the formatting targets. If a
tool is unavailable, report which check could not run rather than claiming validation succeeded.

## Versions, releases, and registry publication

Use `make bump LEVEL=patch|minor|major` for an established package and commit the resulting
manifest change with the release preparation. Use patch for compatible fixes, minor for compatible
features, and major for incompatible behavior or configuration changes.

`make release` validates a clean `main` branch synchronized with `origin/main`, creates an annotated
`<package>-v<version>` tag, and pushes it. The release workflow publishes the deterministic archive
and checksum. Do not create or push tags manually, and never run a release as an incidental part of
implementation.

Registry publication is optional and separate from releasing the widget. A package can always be
installed directly from a checkout or archive. Only add or update official registry metadata after
the release archive and SHA-256 exist.

## Definition of done

A widget change is complete when its identity and manifest are consistent, behavior and settings
are documented, named Lua functions are described, focused regression tests cover the change,
formatting and validation pass, and generated artifacts remain untracked. Report the files changed,
checks run, and any validation not performed.
