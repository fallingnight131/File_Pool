#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/../backend" && pwd)"
WORKERS="${WORKERS:-2}"
BIND="${BIND:-127.0.0.1:5001}"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "错误：未找到 python3.11 或 python3。"
    exit 1
  fi
fi

if ! "${PYTHON_BIN}" - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 8) else 1)
PY
then
  echo "错误：${PYTHON_BIN} 版本过低，需 Python >= 3.8（Flask 3.x 要求）。"
  "${PYTHON_BIN}" --version || true
  exit 1
fi

cd "${BACKEND_DIR}"
if [[ ! -d .venv ]]; then
  "${PYTHON_BIN}" -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
gunicorn -w "${WORKERS}" -b "${BIND}" app:app
