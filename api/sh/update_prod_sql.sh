#!/bin/sh
set -eu

# 手动将指定 SQL 文件执行到生产 PostgreSQL 数据库。
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
COMPOSE_DIR="$(cd "${SCRIPT_DIR}/../docker" && pwd)"

DB_CONTAINER="${DB_CONTAINER:-}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-child_reward}"
SQL_FILE="${1:-}"

if [ -z "${SQL_FILE}" ]; then
  echo "用法：$0 <SQL文件路径>"
  echo "示例：$0 ../../database/migration_family_member_role_incremental.sql"
  exit 1
fi

case "${SQL_FILE}" in
  /*) ;;
  *) SQL_FILE="$(pwd)/${SQL_FILE}" ;;
esac

if [ ! -f "${SQL_FILE}" ]; then
  echo "SQL 文件不存在：${SQL_FILE}"
  exit 1
fi

cd "${COMPOSE_DIR}"

# 确保生产数据库容器已经启动，避免在容器未运行时执行 SQL。
docker compose up -d db

# 优先使用当前 compose 项目中的 db 服务容器，允许生产环境用 DB_CONTAINER 手动覆盖。
if [ -z "${DB_CONTAINER}" ]; then
  DB_CONTAINER="$(docker compose ps -q db)"
fi

if [ -z "${DB_CONTAINER}" ]; then
  echo "未找到 db 服务容器，请先检查 docker compose 配置。"
  exit 1
fi

# 等待数据库可用，避免容器刚启动时 psql 连接失败。
until docker exec "${DB_CONTAINER}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  sleep 1
done

echo "即将执行 SQL 文件：${SQL_FILE}"
echo "目标数据库容器：${DB_CONTAINER}"
echo "目标数据库：${DB_NAME}"
printf "确认要把该 SQL 执行到生产数据库吗？输入 yes 继续："
read -r CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
  echo "已取消执行。"
  exit 0
fi

CONTAINER_SQL_FILE="/tmp/$(basename "${SQL_FILE}")"

# 将宿主机上的 SQL 文件复制到数据库容器中，避免容器无法访问宿主机路径。
docker cp "${SQL_FILE}" "${DB_CONTAINER}:${CONTAINER_SQL_FILE}"

# 使用 ON_ERROR_STOP 保证任意 SQL 失败都会立即退出，避免失败后继续执行后续 SQL。
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${CONTAINER_SQL_FILE}"

# 清理容器内临时 SQL 文件，避免长期占用容器磁盘空间。
docker exec "${DB_CONTAINER}" rm -f "${CONTAINER_SQL_FILE}"

echo "SQL 执行完成：${SQL_FILE}"
