#!/usr/bin/env bash
# ─── Database backup script ────────────────────────────────────────────
# Dumps the PostgreSQL database and prunes backups older than 7 days.
#
# Usage (standalone):
#   DB_PASSWORD=secret ./scripts/backup.sh
#
# Usage (docker-compose — env vars come from the service definition):
#   ./scripts/backup.sh
#
# Environment variables:
#   DB_HOST       — default: db
#   DB_PORT       — default: 5432
#   DB_USER       — default: leadgen
#   DB_PASSWORD   — required
#   DB_NAME       — default: leadgen
#   BACKUP_DIR    — default: /backups
# =======================================================================

set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-leadgen}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
DB_NAME="${DB_NAME:-leadgen}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/leadgen-agent-${TIMESTAMP}.sql.gz"

echo "[backup] Starting pg_dump: ${DB_NAME}@${DB_HOST}:${DB_PORT} → ${BACKUP_FILE}"

PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-acl \
    --compress=9 \
    > "${BACKUP_FILE}"

echo "[backup] Dump complete: $(du -h "${BACKUP_FILE}" | cut -f1)"

# ── Prune backups older than 7 days ────────────────────────────────────
echo "[backup] Pruning backups older than 7 days…"
find "${BACKUP_DIR}" -name "leadgen-agent-*.sql.gz" -type f -mtime +7 -delete
find "${BACKUP_DIR}" -name "leadgen-agent-*.sql.gz" -type f -mtime +7 -exec echo "  deleted: {}" \;

echo "[backup] Remaining backups:"
ls -lh "${BACKUP_DIR}" 2>/dev/null
echo "[backup] Done."
