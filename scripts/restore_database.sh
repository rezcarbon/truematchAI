#!/bin/bash
################################################################################
# TrueMatch PostgreSQL Database Restore Script
#
# Usage: ./restore_database.sh <backup_file> [target_database]
#
# Examples:
#   ./restore_database.sh ./backups/truematch_backup_20240607_020000.sql.gz
#   ./restore_database.sh ./backups/truematch_backup_20240607_020000.sql.gz truematch_restored
#
# WARNING: This script will DROP the target database before restoring.
#          Make sure you have a backup!
#
################################################################################

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-127.0.0.1}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_USER="${DATABASE_USER:-truematch}"
DB_ADMIN_USER="${DB_ADMIN_USER:-postgres}"
TARGET_DB="${2:-truematch}"
BACKUP_FILE="${1}"
LOG_FILE="./restore_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Validate arguments
if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file> [target_database]"
    echo ""
    echo "Example:"
    echo "  $0 ./backups/truematch_backup_20240607_020000.sql.gz"
    echo "  $0 ./backups/truematch_backup_20240607_020000.sql.gz truematch_restored"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    log "❌ Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Function to verify backup
verify_backup() {
    log "Verifying backup integrity..."
    if gunzip -t "${BACKUP_FILE}" > /dev/null 2>&1; then
        log "✅ Backup verification passed"
        return 0
    else
        log "❌ Backup is corrupted"
        return 1
    fi
}

# Function to check database connectivity
check_connectivity() {
    log "Checking database connectivity..."
    if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_ADMIN_USER}" > /dev/null 2>&1; then
        log "❌ Cannot reach database at ${DB_HOST}:${DB_PORT}"
        exit 1
    fi
    log "✅ Database is reachable"
}

# Function to drop existing database
drop_database() {
    local db_name="$1"
    log "Dropping existing database: ${db_name}..."

    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_ADMIN_USER}" \
        -tc "SELECT 1 FROM pg_database WHERE datname = '${db_name}'" | grep -q 1

    if [ $? -eq 0 ]; then
        log "Database ${db_name} exists, terminating connections and dropping..."
        PGPASSWORD="${POSTGRES_PASSWORD}" psql \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_ADMIN_USER}" \
            -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${db_name}' AND pid != pg_backend_pid();" > /dev/null 2>&1 || true

        PGPASSWORD="${POSTGRES_PASSWORD}" dropdb \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_ADMIN_USER}" \
            "${db_name}" >> "${LOG_FILE}" 2>&1

        log "✅ Database dropped"
    else
        log "Database ${db_name} doesn't exist, skipping drop"
    fi
}

# Function to create database
create_database() {
    local db_name="$1"
    log "Creating database: ${db_name}..."

    PGPASSWORD="${POSTGRES_PASSWORD}" createdb \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_ADMIN_USER}" \
        -O "${DB_USER}" \
        "${db_name}" >> "${LOG_FILE}" 2>&1

    log "✅ Database created"
}

# Function to restore from backup
restore_backup() {
    local db_name="$1"
    log "Restoring backup to database: ${db_name}..."

    if zcat "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_ADMIN_USER}" \
        -d "${db_name}" \
        --no-password >> "${LOG_FILE}" 2>&1; then
        log "✅ Backup restored successfully"
        return 0
    else
        log "❌ Restore failed"
        return 1
    fi
}

# Function to verify restore
verify_restore() {
    local db_name="$1"
    log "Verifying restore..."

    local table_count=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_ADMIN_USER}" \
        -d "${db_name}" \
        -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null)

    if [ "${table_count}" -gt 0 ]; then
        log "✅ Restore verification passed (${table_count} tables found)"
        return 0
    else
        log "❌ Restore verification failed (no tables found)"
        return 1
    fi
}

# Function to generate summary
summary() {
    local backup_size=$(du -h "${BACKUP_FILE}" | cut -f1)

    log ""
    log "=================================="
    log "Restore Summary"
    log "=================================="
    log "Source Backup: ${BACKUP_FILE}"
    log "Backup Size: ${backup_size}"
    log "Target Database: ${TARGET_DB}"
    log "Target Host: ${DB_HOST}:${DB_PORT}"
    log "Target User: ${DB_USER}"
    log "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log "Status: SUCCESS"
    log "=================================="
    log "Next steps:"
    log "1. Verify data integrity in ${TARGET_DB}"
    log "2. Test application connectivity"
    log "3. Run database migrations if needed"
    log "4. Backup original database if swapping (rename databases)"
    log "=================================="
    log ""
}

# Confirmation prompt
confirm_restore() {
    echo ""
    echo "⚠️  WARNING: This will DROP and RESTORE the database!"
    echo ""
    echo "Source Backup: ${BACKUP_FILE}"
    echo "Target Database: ${TARGET_DB}"
    echo "Target Host: ${DB_HOST}:${DB_PORT}"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no) " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
}

# Main restore process
main() {
    log "Starting database restore..."

    # Verify backup
    if ! verify_backup; then
        exit 1
    fi

    # Check connectivity
    check_connectivity

    # Confirm with user
    confirm_restore

    # Drop old database
    drop_database "${TARGET_DB}"

    # Create new database
    create_database "${TARGET_DB}"

    # Restore backup
    if ! restore_backup "${TARGET_DB}"; then
        log "❌ Restore failed"
        exit 1
    fi

    # Verify restore
    if ! verify_restore "${TARGET_DB}"; then
        exit 1
    fi

    # Summary
    summary
}

# Execute main function
main "$@"
