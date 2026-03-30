#!/bin/sh
# test_restore.sh — Verifica que el último backup puede restaurarse (H5)
# =============================================================================
# Ejecutar manualmente o desde CI/staging para validar que el backup es
# funcional antes de depender de él en una emergencia.
#
# Proceso:
#   1. Selecciona el backup más reciente en /backups/
#   2. Crea una BD temporal (restore_test_YYYYMMDD)
#   3. Restaura el dump en la BD temporal
#   4. Verifica que la BD contiene al menos N tablas de Odoo esperadas
#   5. Elimina la BD temporal
#   6. Retorna 0 si OK, 1 si falla
#
# Variables de entorno:
#   POSTGRES_USER      (default: odoo)
#   POSTGRES_PASSWORD  (leída de PGPASSWORD)
#   DB_HOST            (default: pg_db)
#   BACKUP_DIR         (default: /backups)
#
# Uso desde el host:
#   docker exec inventory_pg_backup /backup/test_restore.sh
#
# Uso desde docker compose (ad-hoc):
#   docker compose run --rm pg_backup /backup/test_restore.sh
# =============================================================================

set -e

DB_HOST="${DB_HOST:-pg_db}"
DB_USER="${POSTGRES_USER:-odoo}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
TEST_DB="restore_test_$(date +%Y%m%d%H%M%S)"
MIN_TABLES=10    # número mínimo de tablas que debe tener una instalación Odoo válida

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RESTORE-TEST] $*"; }
fail() { log "ERROR: $*"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Seleccionar backup más reciente
# ---------------------------------------------------------------------------
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    fail "No se encontraron backups en ${BACKUP_DIR}"
fi

log "Backup seleccionado: ${LATEST_BACKUP}"
BACKUP_SIZE=$(du -h "${LATEST_BACKUP}" | cut -f1)
log "Tamaño del backup: ${BACKUP_SIZE}"

# ---------------------------------------------------------------------------
# 2. Crear BD temporal para restauración
# ---------------------------------------------------------------------------
log "Creando BD temporal: ${TEST_DB}"
createdb -h "${DB_HOST}" -U "${DB_USER}" "${TEST_DB}" || \
    fail "No se pudo crear la BD temporal ${TEST_DB}"

cleanup() {
    log "Limpiando BD temporal: ${TEST_DB}"
    dropdb -h "${DB_HOST}" -U "${DB_USER}" --if-exists "${TEST_DB}" 2>/dev/null || true
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# 3. Restaurar dump
# ---------------------------------------------------------------------------
log "Restaurando backup en ${TEST_DB}..."
gunzip -c "${LATEST_BACKUP}" | \
    psql -h "${DB_HOST}" -U "${DB_USER}" "${TEST_DB}" -q || \
    fail "Error al restaurar el backup"

log "Restauración completada."

# ---------------------------------------------------------------------------
# 4. Verificar integridad básica — contar tablas de Odoo
# ---------------------------------------------------------------------------
TABLE_COUNT=$(psql -h "${DB_HOST}" -U "${DB_USER}" "${TEST_DB}" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")

log "Tablas encontradas en la BD restaurada: ${TABLE_COUNT}"

if [ "${TABLE_COUNT}" -lt "${MIN_TABLES}" ]; then
    fail "La BD restaurada tiene solo ${TABLE_COUNT} tablas (mínimo esperado: ${MIN_TABLES}). \
El backup podría estar corrupto o incompleto."
fi

# Verificar presencia de tablas críticas de Odoo
for TABLE in res_users stock_quant product_template ir_model; do
    EXISTS=$(psql -h "${DB_HOST}" -U "${DB_USER}" "${TEST_DB}" -tAc \
        "SELECT COUNT(*) FROM information_schema.tables \
         WHERE table_schema = 'public' AND table_name = '${TABLE}'")
    if [ "${EXISTS}" -eq 0 ]; then
        fail "Tabla crítica '${TABLE}' no encontrada en la BD restaurada."
    fi
done

log "Verificación de integridad: OK (${TABLE_COUNT} tablas, tablas críticas presentes)"

# ---------------------------------------------------------------------------
# 5. Reporte final
# ---------------------------------------------------------------------------
log "========================================================"
log "RESULTADO: Backup válido y restaurable"
log "  Archivo:    ${LATEST_BACKUP}"
log "  Tamaño:     ${BACKUP_SIZE}"
log "  Tablas:     ${TABLE_COUNT}"
log "========================================================"
