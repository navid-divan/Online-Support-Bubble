#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ="$HERE/osb"
[ -f "$PROJ/pyproject.toml" ] || PROJ="$HERE"

cd "$PROJ"
VENV="$PROJ/.venv"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  echo "[osb] first run: creating virtualenv and installing (one-time)..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --disable-pip-version-check -e ".[dev]"
elif ! "$PY" -c "import osb" 2>/dev/null; then
  echo "[osb] installing package..."
  "$VENV/bin/pip" install -q --disable-pip-version-check -e ".[dev]"
fi

CMD="${1:-shell}"
echo "[osb] running: $CMD   (options: shell | demo | test | info)"
echo

case "$CMD" in
  test) exec "$PY" -m pytest ;;
  *)    exec "$PY" -m osb "$CMD" ;;
esac
