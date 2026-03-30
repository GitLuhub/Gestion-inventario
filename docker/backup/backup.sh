#!/bin/sh
# backup.sh — Backup automatizado de PostgreSQL para inventory_custom
# Se ejecuta como cron dentro del contenedor pg_backup (perfil: production)
# Variables de entorno requeridas: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
#   BACKUP_RETENTION_DAYS (default: 7)

set -e

BACKUP_DIR="/backups"
DB_HOST="pg_db"
DB_NAME="${POSTGRES_DB:-odoo_db}"
DB_USER="${POSTGRES_USER:-odoo}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup de ${DB_NAME}..."

pg_dump -h "${DB_HOST}" -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completado: ${BACKUP_FILE}"

# Eliminar backups más antiguos que RETENTION_DAYS
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

REMAINING=$(find "${BACKUP_DIR}" -name "*.sql.gz" | wc -l)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backups retenidos: ${REMAINING} (retención: ${RETENTION_DAYS} días)"
