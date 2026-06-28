#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
PORT="${1:-8000}"

echo "Serving the OSB web app at http://localhost:${PORT}"
echo "Open http://localhost:${PORT}/index.html  (Ctrl-C to stop)"
exec python3 -m http.server "$PORT"
