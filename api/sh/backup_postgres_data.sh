#!/bin/sh
set -eu

# 备份当前 Docker 环境中的 PostgreSQL 业务数据。
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
COMPOSE_DIR="$(cd "${SCRIPT_DIR}/../docker" && pwd)"
DB_DATA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/db_data"

DB_CONTAINER="${DB_CONTAINER:-}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-child_reward}"
BACKUP_FILE="${1:-${DB_DATA_DIR}/child_reward_$(date +%Y%m%d_%H%M%S).dump}"
CONTAINER_BACKUP_FILE="/tmp/$(basename "${BACKUP_FILE}")"

case "${BACKUP_FILE}" in
  /*) ;;
  *) BACKUP_FILE="$(pwd)/${BACKUP_FILE}" ;;
esac

mkdir -p "$(dirname "${BACKUP_FILE}")"

cd "${COMPOSE_DIR}"

# 确保数据库容器已经启动，避免在容器未运行时直接备份失败。
docker compose up -d db

# 优先使用当前 compose 项目中的 db 服务容器，避免固定容器名在不同环境失效。
if [ -z "${DB_CONTAINER}" ]; then
  DB_CONTAINER="$(docker compose ps -q db)"
fi

if [ -z "${DB_CONTAINER}" ]; then
  echo "未找到 db 服务容器，请先检查 docker compose 配置。"
  exit 1
fi

# 使用 PostgreSQL 自定义格式导出，方便新环境用 pg_restore 恢复。
docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -Fc -f "${CONTAINER_BACKUP_FILE}"

# 将容器内备份文件复制到宿主机，便于拷贝到新环境。
docker cp "${DB_CONTAINER}:${CONTAINER_BACKUP_FILE}" "${BACKUP_FILE}"

# 清理容器内临时备份文件，避免长期占用容器磁盘空间。
docker exec "${DB_CONTAINER}" rm -f "${CONTAINER_BACKUP_FILE}"

echo "PostgreSQL 数据备份完成：${BACKUP_FILE}"
