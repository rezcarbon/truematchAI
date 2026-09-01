#!/bin/bash
################################################################################
# TrueMatch PostgreSQL Database Backup Script
#
# Usage: ./backup_database.sh
#
# Configuration:
#   - Backup directory: ./backups/
#   - Retention period: 30 days
#   - Compression: gzip
#   - Schedule: Use cron for automated daily backups
#
# Cron example (daily at 2 AM):
#   0 2 * * * /path/to/TrueMatch/scripts/backup_database.sh
#
################################################################################

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-127.0.0.1}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_USER="${DATABASE_USER:-truematch}"
DB_NAME="${DATABASE_NAME:-truematch}"
BACKUP_DIR="./backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/truematch_backup_${TIMESTAMP}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Function to clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -name "truematch_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    local removed_count=$(find "${BACKUP_DIR}" -name "truematch_backup_*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l)
    if [ "${removed_count}" -gt 0 ]; then
        log "Removed ${removed_count} old backup(s)"
    else
        log "No old backups to remove"
    fi
}

# Function to verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."
    if gunzip -t "${BACKUP_FILE}" > /dev/null 2>&1; then
        log "✅ Backup verification passed"
        return 0
    else
        log "❌ Backup verification failed"
        return 1
    fi
}

# Function to generate backup summary
summary() {
    local backup_size=$(du -h "${BACKUP_FILE}" | cut -f1)
    local row_count=$(zcat "${BACKUP_FILE}" | grep -c "INSERT INTO" || echo "unknown")

    log ""
    log "=================================="
    log "Backup Summary"
    log "=================================="
    log "Database: ${DB_NAME}"
    log "Host: ${DB_HOST}:${DB_PORT}"
    log "Backup File: ${BACKUP_FILE}"
    log "Backup Size: ${backup_size}"
    log "Timestamp: ${TIMESTAMP}"
    log "Status: SUCCESS"
    log "=================================="
    log ""
}

# Main backup process
main() {
    log "Starting database backup..."
    log "Database: ${DB_NAME}"
    log "Host: ${DB_HOST}:${DB_PORT}"
    log "User: ${DB_USER}"

    # Check if database is reachable
    if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" > /dev/null 2>&1; then
        log "❌ Cannot reach database at ${DB_HOST}:${DB_PORT}"
        exit 1
    fi

    log "✅ Database is reachable"

    # Perform the backup
    log "Dumping database..."
    if PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --no-password 2>>"${LOG_FILE}" | gzip > "${BACKUP_FILE}"; then
        log "✅ Database dump completed"
    else
        log "❌ Database dump failed"
        exit 1
    fi

    # Verify the backup
    if verify_backup; then
        log "✅ Backup successfully created"
    else
        log "❌ Backup verification failed, removing corrupted file"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi

    # Cleanup old backups
    cleanup_old_backups

    # Generate summary
    summary
}

# Execute main function
main "$@"
