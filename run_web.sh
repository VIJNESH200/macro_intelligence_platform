#!/usr/bin/env bash
#
# Start the Macro Intelligence Platform web interface on port 8000.
# The matplotlib desktop app is unaffected -- that is still `python main.py`.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

URL="http://127.0.0.1:8000"

bold=$'\033[1m'; dim=$'\033[2m'; green=$'\033[32m'; off=$'\033[0m'

# Without a build the page 404s instead of failing loudly, so make it on demand.
if [[ ! -f web/frontend/dist/index.html ]]; then
  printf '%s\n' "${dim}No frontend build found — building it now (one-off, ~30s)…${off}"
  pushd web/frontend >/dev/null
  [[ -d node_modules ]] || npm install --no-fund --no-audit
  npm run build
  popd >/dev/null
  printf '\n'
fi

printf '%s\n'   "${bold}Macro Intelligence Platform${off}"
printf '  %s\n' "${green}${URL}${off}   ${dim}← open this${off}"
printf '  %s\n' "${dim}${URL}/docs   API reference${off}"
printf '\n  %s\n\n' "${dim}Ctrl-C to stop.${off}"

# First request loads and caches the market data, so it takes a few seconds.
exec python3 -m uvicorn web.server:app --host 127.0.0.1 --port 8000
