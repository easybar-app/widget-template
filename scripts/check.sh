#!/usr/bin/env bash
# Validate the widget package and its Lua sources.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
lua_bin="${LUA:-lua}"

command -v "${lua_bin}" >/dev/null 2>&1 || {
  echo "Lua 5.5 is required: ${lua_bin}" >&2
  exit 1
}
"${lua_bin}" -e 'assert(_VERSION == "Lua 5.5", "expected Lua 5.5, got " .. tostring(_VERSION))'

while IFS= read -r file; do
  LUA_CHECK_FILE="${file}" "${lua_bin}" -e \
    'local path = assert(os.getenv("LUA_CHECK_FILE")); assert(loadfile(path, "t", {}))'
done < <(find "${repo_root}" -type f -name '*.lua' -not -path '*/.git/*' -print | LC_ALL=C sort)

"${lua_bin}" "${repo_root}/tests/test.lua" "${repo_root}"
