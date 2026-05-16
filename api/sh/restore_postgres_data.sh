#!/usr/bin/env bash
set -euo pipefail

# 将备份文件导入到当前 Docker 环境中的 PostgreSQL 数据库。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "${SCRIPT_DIR}/../docker" && pwd)"
DB_DATA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/db_data"

DB_CONTAINER="${DB_CONTAINER:-child_reward_db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-child_reward}"
BACKUP_FILE="${1:-}"

if [[ -z "${BACKUP_FILE}" ]]; then
  echo "用法：$0 <备份文件路径>"
  echo "示例：$0 ${DB_DATA_DIR}/child_reward_20260516_120000.dump"
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "备份文件不存在：${BACKUP_FILE}"
  exit 1
fi

cd "${COMPOSE_DIR}"

# 确保新环境数据库容器已经启动。
docker compose up -d db

# 等待数据库可用，避免容器刚启动时导入失败。
until docker exec "${DB_CONTAINER}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  sleep 1
done

CONTAINER_BACKUP_FILE="/tmp/$(basename "${BACKUP_FILE}")"

# 将宿主机上的备份文件复制到新环境数据库容器中。
docker cp "${BACKUP_FILE}" "${DB_CONTAINER}:${CONTAINER_BACKUP_FILE}"

# 清空并重建业务库，保证导入结果与老环境备份一致。
docker exec "${DB_CONTAINER}" dropdb -U "${DB_USER}" --if-exists "${DB_NAME}"
docker exec "${DB_CONTAINER}" createdb -U "${DB_USER}" "${DB_NAME}"
docker exec "${DB_CONTAINER}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" "${CONTAINER_BACKUP_FILE}"

# 清理容器内临时备份文件。
docker exec "${DB_CONTAINER}" rm -f "${CONTAINER_BACKUP_FILE}"

echo "PostgreSQL 数据导入完成：${DB_NAME}"
