#!/bin/sh
set -eu

# 拉取最新代码后，重新构建并启动 Docker Compose 中的 API 后端服务。
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
API_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_DIR="$(cd "${API_DIR}/docker" && pwd)"

API_SERVICE="${API_SERVICE:-api}"
GIT_TIMEOUT="${GIT_TIMEOUT:-60}"
BUILD_TIMEOUT="${BUILD_TIMEOUT:-600}"
UP_TIMEOUT="${UP_TIMEOUT:-120}"
PULL_BASE_IMAGE="${PULL_BASE_IMAGE:-false}"

run_with_timeout() {
  seconds="$1"
  step="$2"
  shift 2

  if ! command -v timeout >/dev/null 2>&1; then
    echo "未找到 timeout 命令，无法为步骤设置超时：${step}"
    echo "请安装 coreutils，或手动执行下面的命令排查："
    printf '  %s' "$@"
    printf '\n'
    exit 1
  fi

  status=0
  timeout "${seconds}s" "$@" || status="$?"
  if [ "${status}" -eq 0 ]; then
    return 0
  fi

  if [ "${status}" -eq 124 ]; then
    echo "${step} 超时（${seconds}s）。请检查网络、代理或 Docker 镜像源配置。"
  else
    echo "${step} 失败，退出码：${status}"
  fi
  exit "${status}"
}

cd "${API_DIR}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "当前目录不是 Git 仓库：${API_DIR}"
  exit 1
fi

BRANCH="$(git branch --show-current)"
if [ -z "${BRANCH}" ]; then
  echo "当前 Git 仓库处于 detached HEAD 状态，请先切换到要更新的分支。"
  exit 1
fi

echo "正在拉取最新代码：${BRANCH}"
run_with_timeout "${GIT_TIMEOUT}" "拉取 Git 代码" \
  env GIT_TERMINAL_PROMPT=0 git pull --ff-only origin "${BRANCH}"

cd "${COMPOSE_DIR}"

echo "正在重新构建 API 服务：${API_SERVICE}"
BUILD_ARGS=""
if [ "${PULL_BASE_IMAGE}" = "true" ]; then
  BUILD_ARGS="--pull"
fi

# 默认不拉取基础镜像，避免 GitHub/Docker Hub 网络异常时表现为长时间无输出。
run_with_timeout "${BUILD_TIMEOUT}" "构建 Docker 镜像" \
  docker compose build --progress=plain ${BUILD_ARGS} "${API_SERVICE}"

echo "正在重启 API 服务：${API_SERVICE}"
run_with_timeout "${UP_TIMEOUT}" "重启 API 服务" \
  docker compose up -d --no-deps "${API_SERVICE}"

echo "API 后端更新完成。"
