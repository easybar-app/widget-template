#!/usr/bin/env python3
"""Validate, version, package, and release a standalone EasyBar widget."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import re
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "package.toml"
SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")
STABLE_SEMVER = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
)
PACKAGE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MODULE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*")
CONSTRAINT = re.compile(r"\^?[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")
VERSION_LINE = re.compile(r'(?m)^version = "([^"]+)"$')
ASSET_LITERAL = re.compile(r'easybar\.asset\("([^"@][^"]*)"\)')
REMOTE = "origin"
BRANCH = "main"


def fail(message: str) -> None:
    """Exit with a validation error."""
    raise ValueError(message)


def load_manifest() -> dict:
    """Load the generator manifest."""
    with MANIFEST_PATH.open("rb") as handle:
        return tomllib.load(handle)


def safe_file(relative: object, label: str) -> Path:
    """Resolve and validate a package-relative file."""
    if not isinstance(relative, str) or not relative:
        fail(f"{label} must be a non-empty string")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        fail(f"unsafe {label}: {relative}")
    resolved = ROOT / path
    if not resolved.is_file() or resolved.is_symlink():
        fail(f"missing or unsafe {label}: {relative}")
    return resolved


def validate_manifest() -> dict:
    """Validate package metadata and declared files."""
    manifest = load_manifest()
    if manifest.get("manifest_version") != 2:
        fail("manifest_version must be 2")
    name = manifest.get("name")
    if not isinstance(name, str) or not PACKAGE_NAME.fullmatch(name):
        fail(f"invalid package name: {name!r}")
    if manifest.get("kind") not in {"widget", "library"}:
        fail("kind must be widget or library")

    for field in ("version", "minimum_easybar_kit_version"):
        value = manifest.get(field)
        if not isinstance(value, str) or not SEMVER.fullmatch(value):
            fail(f"invalid {field}: {value!r}")
    for field in ("description", "license", "readme"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            fail(f"missing {field}")

    safe_file(manifest["readme"], "readme")
    declared_lua: set[Path] = set()
    if manifest["kind"] == "widget":
        entrypoint = safe_file(manifest.get("entrypoint"), "entrypoint")
        if entrypoint.suffix.lower() != ".lua":
            fail("entrypoint must be Lua")
        declared_lua.add(entrypoint)
    elif "entrypoint" in manifest:
        fail("library packages cannot declare an entrypoint")

    exports = manifest.get("exports", {})
    if not isinstance(exports, dict):
        fail("exports must be a table")
    for module, relative in exports.items():
        if not isinstance(module, str) or not MODULE_NAME.fullmatch(module):
            fail(f"invalid exported module: {module!r}")
        exported = safe_file(relative, f"export {module}")
        if exported.suffix.lower() != ".lua":
            fail(f"export {module} must be Lua")
        declared_lua.add(exported)

    actual_lua = {
        path
        for path in ROOT.rglob("*.lua")
        if path.relative_to(ROOT).parts[0] not in {"tests", ".git"}
    }
    undeclared = sorted(path.relative_to(ROOT) for path in actual_lua - declared_lua)
    if undeclared:
        fail(f"undeclared Lua files: {', '.join(map(str, undeclared))}")

    dependencies = manifest.get("dependencies", {})
    if not isinstance(dependencies, dict):
        fail("dependencies must be a table")
    for dependency, constraint in dependencies.items():
        if not isinstance(dependency, str) or not PACKAGE_NAME.fullmatch(dependency):
            fail(f"invalid dependency: {dependency!r}")
        if dependency == name:
            fail("package cannot depend on itself")
        if not isinstance(constraint, str) or not CONSTRAINT.fullmatch(constraint):
            fail(f"invalid dependency constraint for {dependency}: {constraint!r}")

    repository = manifest.get("repository")
    if repository is not None:
        if not isinstance(repository, dict) or not isinstance(repository.get("url"), str):
            fail("repository.url must be a string")
        parsed = urlparse(repository["url"])
        if parsed.scheme != "https" or not parsed.netloc:
            fail("repository.url must be an HTTPS URL")

    for lua_path in actual_lua:
        source = lua_path.read_text(encoding="utf-8")
        for asset in ASSET_LITERAL.findall(source):
            safe_file(asset, f"asset referenced by {lua_path.name}")
    return manifest


def command_validate(_: argparse.Namespace) -> None:
    """Handle the validate command."""
    manifest = validate_manifest()
    print(f"Validated EasyBar package {manifest['name']}.")


def archive_info(name: str, size: int) -> tarfile.TarInfo:
    """Create normalized metadata for an archive entry."""
    info = tarfile.TarInfo(name)
    info.size = size
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def package_files(manifest: dict) -> list[tuple[str, Path]]:
    """Collect files included in a release archive."""
    selected = {
        MANIFEST_PATH,
        safe_file(manifest.get("readme"), "readme"),
    }
    if manifest.get("kind") == "widget":
        selected.add(safe_file(manifest.get("entrypoint"), "entrypoint"))
    for module, relative in manifest.get("exports", {}).items():
        selected.add(safe_file(relative, f"export {module}"))

    license_path = ROOT / "LICENSE"
    if license_path.is_file():
        selected.add(license_path)
    assets = ROOT / "assets"
    if assets.exists():
        for path in assets.rglob("*"):
            if path.is_symlink():
                fail(f"symbolic links are not allowed: {path.relative_to(ROOT)}")
            if path.is_file():
                selected.add(path)
    return sorted((path.relative_to(ROOT).as_posix(), path) for path in selected)


def write_archive(files: list[tuple[str, Path]], archive_path: Path) -> str:
    """Write a deterministic package archive."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for relative, path in files:
                    data = path.read_bytes()
                    archive.addfile(archive_info(relative, len(data)), io.BytesIO(data))

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    return digest


def command_package(args: argparse.Namespace) -> None:
    """Handle the package command."""
    manifest = validate_manifest()
    name = manifest["name"]
    version = manifest["version"]
    if args.version is not None and args.version != version:
        fail(f"requested version {args.version} does not match manifest {version}")
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    archive_path = output_dir / f"{name}-{version}.tar.gz"
    digest = write_archive(package_files(manifest), archive_path)
    print(f"archive={archive_path.resolve()}")
    print(f"sha256={digest}")
    print(f"name={name}")
    print(f"version={version}")


def bumped_version(version: str, level: str) -> str:
    """Return a version with the requested component bumped."""
    match = STABLE_SEMVER.fullmatch(version)
    if match is None:
        fail(f"version must be stable semantic version: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def command_bump(args: argparse.Namespace) -> None:
    """Handle the bump command."""
    manifest = validate_manifest()
    current = manifest["version"]
    updated = bumped_version(current, args.level)
    source = MANIFEST_PATH.read_text(encoding="utf-8")
    if VERSION_LINE.findall(source) != [current]:
        fail("expected one canonical version field")
    MANIFEST_PATH.write_text(VERSION_LINE.sub(f'version = "{updated}"', source, count=1), encoding="utf-8")
    print(f"Bumped package from {current} to {updated} ({args.level}).")


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run Git with captured text output."""
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def release_preflight(tag: str) -> str:
    """Validate repository state before a release."""
    if git("status", "--porcelain=v1", "--untracked-files=all").stdout.strip():
        fail("worktree must be clean before creating a release")
    branch = git("branch", "--show-current").stdout.strip()
    if branch != BRANCH:
        fail(f"release must be created from {BRANCH}, not {branch or 'detached HEAD'}")
    git("fetch", REMOTE, BRANCH)
    head = git("rev-parse", "HEAD").stdout.strip()
    remote_head = git("rev-parse", f"{REMOTE}/{BRANCH}").stdout.strip()
    if head != remote_head:
        fail(f"local {BRANCH} must exactly match {REMOTE}/{BRANCH}")
    if git("show-ref", "--verify", "--quiet", f"refs/tags/{tag}", check=False).returncode == 0:
        fail(f"tag already exists locally: {tag}")
    remote_tag = git("ls-remote", "--exit-code", "--tags", REMOTE, f"refs/tags/{tag}", check=False)
    if remote_tag.returncode == 0:
        fail(f"tag already exists on {REMOTE}: {tag}")
    if remote_tag.returncode != 2:
        fail(remote_tag.stderr.strip() or "unable to inspect remote tags")
    return head


def command_release(args: argparse.Namespace) -> None:
    """Handle the release command."""
    manifest = validate_manifest()
    name = manifest["name"]
    version = manifest["version"]
    tag = f"{name}-v{version}"
    head = release_preflight(tag)
    if not args.publish:
        print(f"Ready to release {tag} from {head[:12]}.")
        return
    git("tag", "-a", tag, "-m", f"Release {name} {version}")
    try:
        git("push", REMOTE, f"refs/tags/{tag}")
    except subprocess.CalledProcessError:
        git("tag", "--delete", tag, check=False)
        raise
    print(f"Published {tag} from {head[:12]}.")


def parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.set_defaults(handler=command_validate)

    package = commands.add_parser("package")
    package.add_argument("--version")
    package.add_argument("--output-dir", type=Path, default=Path("dist"))
    package.set_defaults(handler=command_package)

    bump = commands.add_parser("bump")
    bump.add_argument("--level", required=True, choices=("major", "minor", "patch"))
    bump.set_defaults(handler=command_bump)

    release = commands.add_parser("release")
    release.add_argument("--publish", action="store_true")
    release.set_defaults(handler=command_release)
    return root


def main() -> int:
    """Run the command-line entry point."""
    args = parser().parse_args()
    try:
        args.handler(args)
    except (OSError, subprocess.CalledProcessError, tarfile.TarError, tomllib.TOMLDecodeError, ValueError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Widget command failed: {detail or error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
