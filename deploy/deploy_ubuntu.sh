#!/usr/bin/env bash
set -euo pipefail

# FilePool 宝塔最小部署脚本
# 用法：
#   bash deploy/deploy_ubuntu.sh /www/wwwroot/filepool /www/wwwroot/filepool/frontend/dist
# 参数：
#   1) PROJECT_DIR 项目目录（默认 /www/wwwroot/filepool）
#   2) WEB_ROOT 前端发布目录（默认 /www/wwwroot/filepool/frontend/dist）
# 环境变量：
#   PYTHON_BIN 指定 Python 解释器（默认自动找 python3.11 或 python3）

PROJECT_DIR="${1:-/www/wwwroot/filepool}"
WEB_ROOT="${2:-/www/wwwroot/filepool/frontend/dist}"
PYTHON_BIN="${PYTHON_BIN:-}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "错误：未找到命令 $1"
    exit 1
  fi
}

detect_python_bin() {
  if [[ -n "${PYTHON_BIN}" ]]; then
    require_command "${PYTHON_BIN}"
    return
  fi

  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "错误：未找到 python3.11 或 python3，请在宝塔安装 Python 3.11。"
    exit 1
  fi
}

ensure_python_version() {
  if ! "${PYTHON_BIN}" - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 8) else 1)
PY
  then
    echo "错误：${PYTHON_BIN} 版本过低，要求 Python >= 3.8。"
    "${PYTHON_BIN}" --version || true
    exit 1
  fi
}

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "错误：项目目录不存在 ${PROJECT_DIR}"
  exit 1
fi

if [[ ! -f "${PROJECT_DIR}/backend/requirements.txt" ]]; then
  echo "错误：未找到后端依赖文件 ${PROJECT_DIR}/backend/requirements.txt"
  exit 1
fi

if [[ ! -f "${PROJECT_DIR}/frontend/package.json" ]]; then
  echo "错误：未找到前端依赖文件 ${PROJECT_DIR}/frontend/package.json"
  exit 1
fi

detect_python_bin
ensure_python_version
require_command npm

echo "[1/4] 配置后端虚拟环境并安装依赖"
cd "${PROJECT_DIR}/backend"
"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[2/4] 构建前端"
cd "${PROJECT_DIR}/frontend"
npm install
npm run build

echo "[3/4] 发布前端"
mkdir -p "${WEB_ROOT}"
rsync -a --delete dist/ "${WEB_ROOT}/"

echo "[4/4] 输出启动提示"
cat <<EOF
部署完成。

后端启动命令：
cd ${PROJECT_DIR}/backend && source .venv/bin/activate && gunicorn -w 2 -b 127.0.0.1:5001 app:app

Nginx 配置文件建议使用：
${PROJECT_DIR}/deploy/nginx-fallingnight-filepool-only.conf

宝塔环境重载 Nginx：
/etc/init.d/nginx reload
EOF
